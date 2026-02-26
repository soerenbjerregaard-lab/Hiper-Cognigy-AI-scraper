'use strict';
// Phase 3 – Multi-turn opfølgningssamtaler (turn 2, 3, 4)
//
// Strategi: Start frisk browser-session per scenarie, replay alle foregående
// user-beskeder for kontekst, gem kun de turns der mangler i DB.
//
// Usage: node phase3_followup.js [--limit N]

const { chromium } = require('playwright');
const { openDb, saveConversation } = require('./db');
const config = require('./config');
const fs = require('fs');
const path = require('path');

const FOLLOWUPS_PATH = path.join(__dirname, 'followups.json');
const CONCURRENCY = config.CONCURRENCY;

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function extractLinks(text) {
  if (!text) return [];
  const urlRegex = /https?:\/\/[^\s<>"')\]]+/g;
  return [...new Set(text.match(urlRegex) || [])];
}

function detectHandover(text) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return config.HANDOVER_TEXT_MARKERS.some(m => lower.includes(m));
}

// Register a single onMessage listener once per page.
// Messages go into a queue; nextBotMessage() pops them in order.
// This avoids the listener-accumulation bug when calling sendAndWait multiple times.
async function setupMessageQueue(page) {
  await page.evaluate(() => {
    window.__botMsgQueue = [];
    window.__botMsgResolvers = [];
    window.cognigyWebChat.onMessage((msg) => {
      if (msg.data && msg.data.handover_available === true) return;
      const text = msg.text || '';
      if (window.__botMsgResolvers.length > 0) {
        window.__botMsgResolvers.shift()(text);
      } else {
        window.__botMsgQueue.push(text);
      }
    });
  });
}

function nextBotMessage(page, timeoutMs = config.TIMEOUT_MS) {
  return page.evaluate((ms) => {
    return new Promise((resolve, reject) => {
      if (window.__botMsgQueue.length > 0) {
        resolve(window.__botMsgQueue.shift());
        return;
      }
      const timer = setTimeout(() => {
        window.__botMsgResolvers.shift(); // remove this resolver so it won't fire later
        reject(new Error('Timeout'));
      }, ms);
      window.__botMsgResolvers.push((text) => {
        clearTimeout(timer);
        resolve(text);
      });
    });
  }, timeoutMs);
}

async function sendAndWait(page, message, timeoutMs) {
  const p = nextBotMessage(page, timeoutMs);
  await page.evaluate(q => window.cognigyWebChat.sendMessage(q), message);
  return p;
}

function hasTurn(db, session_id, turn) {
  return db.prepare(
    "SELECT COUNT(*) as n FROM conversations WHERE session_id = ? AND turn = ? AND role = 'bot'"
  ).get(session_id, turn).n > 0;
}

async function runFollowup(browser, db, entry, label) {
  const {
    session_id, category, category_tag,
    original_question, followup_1, followup_2, followup_3
  } = entry;
  const meta = { category, category_tag: category_tag || null };

  // Bestem hvilke turns der mangler
  const need2 = !hasTurn(db, session_id, 2);
  const need3 = followup_2 && !hasTurn(db, session_id, 3);
  const need4 = followup_3 && !hasTurn(db, session_id, 4);

  if (!need2 && !need3 && !need4) {
    console.log(`${label} ↩ skip`);
    return;
  }

  const ctx = await browser.newContext();
  const page = await ctx.newPage();

  try {
    await page.goto(config.ENDPOINT, { waitUntil: 'networkidle' });
    await sleep(config.PAGE_LOAD_WAIT);

    // Registrér én samlet message-queue listener (undgår listener-akkumulering ved 4 turns)
    await setupMessageQueue(page);

    // Åbn chat og klik #new_customer
    await page.evaluate(() => window.cognigyWebChat.open());
    await page.waitForFunction(
      () => document.querySelector('iframe[class*="cognigy-webchat"]') !== null,
      { timeout: 10000 }
    );
    await sleep(1000);
    const srcdocFrame = page.frames().find(f => f.url() === 'about:srcdoc');
    await srcdocFrame.locator('#new_customer').click({ force: true });
    try { await nextBotMessage(page, 15000); } catch {}
    await sleep(800);

    // Turn 1: original spørgsmål (kontekst – gemmes ikke)
    const bot1 = await sendAndWait(page, original_question, config.TIMEOUT_MS);
    await sleep(1000);

    // Turn 2: followup_1
    const bot2 = await sendAndWait(page, followup_1, config.TIMEOUT_MS);
    if (need2) {
      saveConversation(db, session_id, meta, 2, 'user', followup_1, false, []);
      saveConversation(db, session_id, meta, 2, 'bot', bot2, detectHandover(bot2), extractLinks(bot2));
    }
    await sleep(1000);

    // Turn 3: followup_2
    let bot3 = null;
    if (followup_2) {
      bot3 = await sendAndWait(page, followup_2, config.TIMEOUT_MS);
      if (need3) {
        saveConversation(db, session_id, meta, 3, 'user', followup_2, false, []);
        saveConversation(db, session_id, meta, 3, 'bot', bot3, detectHandover(bot3), extractLinks(bot3));
      }
      await sleep(1000);
    }

    // Turn 4: followup_3 (uddybende)
    let bot4 = null;
    if (followup_3) {
      bot4 = await sendAndWait(page, followup_3, config.TIMEOUT_MS);
      if (need4) {
        saveConversation(db, session_id, meta, 4, 'user', followup_3, false, []);
        saveConversation(db, session_id, meta, 4, 'bot', bot4, detectHandover(bot4), extractLinks(bot4));
      }
    }

    const allBots = [bot2, bot3, bot4].filter(Boolean);
    const anyHandover = allBots.some(b => detectHandover(b));
    const turns = [need2 && 2, need3 && 3, need4 && 4].filter(Boolean);
    console.log(`${label} ✓ turns saved: [${turns.join(',')}]${anyHandover ? ' [HANDOVER]' : ''}`);

  } catch (err) {
    console.log(`${label} ✗ ${err.message}`);
  } finally {
    await ctx.close();
  }
}

async function main() {
  if (!fs.existsSync(FOLLOWUPS_PATH)) {
    console.error('FEJL: followups.json ikke fundet.');
    process.exit(1);
  }

  const followups = JSON.parse(fs.readFileSync(FOLLOWUPS_PATH, 'utf8'));
  const db = openDb();

  const limitArg = process.argv.indexOf('--limit');
  const limitVal = limitArg !== -1 ? parseInt(process.argv[limitArg + 1], 10) : followups.length;
  const queue = followups.slice(0, limitVal).map((e, i) => ({ entry: e, i: i + 1 }));
  const total = queue.length;

  console.log(`\n=== Phase 3 – Multi-turn samtaler (turn 2/3/4) ===`);
  console.log(`${total} sessioner, ${CONCURRENCY} parallelle\n`);

  const browser = await chromium.launch({ headless: config.HEADLESS });

  async function worker() {
    while (queue.length > 0) {
      const { entry, i } = queue.shift();
      const label = `[${i}/${total}] ${entry.category}:`;
      await runFollowup(browser, db, entry, label);
      if (queue.length > 0) {
        await sleep(config.DELAY_MIN + Math.random() * (config.DELAY_MAX - config.DELAY_MIN));
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  await browser.close();

  const counts = [2,3,4].map(t =>
    db.prepare(`SELECT COUNT(*) as n FROM conversations WHERE turn=? AND role='bot'`).get(t).n
  );
  console.log(`\n=== Færdig ===`);
  console.log(`Turn 2: ${counts[0]}  Turn 3: ${counts[1]}  Turn 4: ${counts[2]}\n`);
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
