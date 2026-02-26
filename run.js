'use strict';
// run.js – Hiper Cognigy AI Scraper
//
// Kører alle 49 scenarier i én kørsel.
// Hvert scenarie åbner en frisk chat-session og sender alle spørgsmål i rækkefølge.
//
// Usage:
//   node run.js                     → alle 49 scenarier
//   node run.js --limit 5           → de første 5 (test)
//   node run.js --concurrency 5     → overstyr parallelitet

const { chromium }   = require('playwright');
const { randomUUID } = require('crypto');
const { openDb, saveConversation } = require('./db');
const config    = require('./config');
const checkLinks = require('./check_links');
const scenarios = require('./scenarios.json');
const fs   = require('fs');
const path = require('path');

// ─── CLI args ────────────────────────────────────────────────────────────────
const arg = (flag, def) => {
  const i = process.argv.indexOf(flag);
  return i !== -1 ? parseInt(process.argv[i + 1], 10) : def;
};
const LIMIT       = arg('--limit', scenarios.length);
const CONCURRENCY = arg('--concurrency', config.CONCURRENCY || 5);
const batch       = scenarios.slice(0, LIMIT);

// ─── Helpers ─────────────────────────────────────────────────────────────────
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function extractLinks(text) {
  if (!text) return [];
  return [...new Set((text.match(/https?:\/\/[^\s<>"')\]]+/g) || []))];
}

function detectHandover(text) {
  if (!text) return false;
  return config.HANDOVER_TEXT_MARKERS.some(m => text.toLowerCase().includes(m));
}

// ─── Message queue ────────────────────────────────────────────────────────────
// Registrerer én onMessage-listener per page; beskeder routes til kø/resolver.
async function setupMessageQueue(page) {
  await page.evaluate(() => {
    window.__botMsgQueue     = [];
    window.__botMsgResolvers = [];
    window.cognigyWebChat.onMessage((msg) => {
      if (msg.data && msg.data.handover_available === true) return;
      const text = msg.text || '';
      if (!text) return; // skip tomme beskeder (quick replies, kort uden tekst)
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
        window.__botMsgResolvers.shift();
        reject(new Error('timeout'));
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
  p.catch(() => {}); // undgå unhandled rejection hvis page lukkes før await
  await page.evaluate(q => window.cognigyWebChat.sendMessage(q), message);
  return p;
}

// ─── CSV export ───────────────────────────────────────────────────────────────
function exportCsv(db) {
  const rows = db.prepare(
    'SELECT * FROM conversations ORDER BY category, session_id, turn, role'
  ).all();
  if (rows.length === 0) return;

  const cols   = Object.keys(rows[0]);
  const now    = new Date();
  const pad    = n => String(n).padStart(2, '0');
  const ts     = `${pad(now.getHours())}.${pad(now.getMinutes())}-${pad(now.getDate())}-${pad(now.getMonth()+1)}-${now.getFullYear()}`;
  const fname  = path.join(__dirname, 'exports', `conversations-${ts}.csv`);
  const escape = v => `"${String(v ?? '').replace(/"/g, '""')}"`;

  const lines = [cols.map(escape).join(',')];
  for (const row of rows) lines.push(cols.map(c => escape(row[c])).join(','));
  fs.writeFileSync(fname, lines.join('\n'), 'utf8');
  console.log(`\nCSV eksporteret → ${path.basename(fname)}  (${rows.length} rækker)`);
}

// ─── Kør ét scenarie ──────────────────────────────────────────────────────────
async function runScenario(browser, db, scenario, label) {
  const { category, category_tag, questions } = scenario;
  const sessionId = randomUUID();
  const meta      = { category, category_tag: category_tag || null };

  const ctx  = await browser.newContext();
  const page = await ctx.newPage();

  const results = []; // { turn, botText }

  try {
    // domcontentloaded er hurtigere end networkidle og mere robust under høj concurrency
    await page.goto(config.ENDPOINT, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await sleep(config.PAGE_LOAD_WAIT);

    // Sæt message-queue op (én listener for hele sessionen)
    await setupMessageQueue(page);

    // Åbn chat
    await page.evaluate(() => window.cognigyWebChat.open());
    // Bemærk: null som andet argument (arg) er nødvendigt for at options virker korrekt
    await page.waitForFunction(
      () => document.querySelector('iframe[class*="cognigy-webchat"]') !== null,
      null,
      { timeout: 15000 }
    );
    await sleep(1000);

    // Klik "Jeg er ikke kunde"
    const srcdocFrame = page.frames().find(f => f.url() === 'about:srcdoc');
    if (!srcdocFrame) throw new Error('srcdoc frame ikke fundet');
    await srcdocFrame.locator('#new_customer').click({ force: true });

    // Vent på velkomstbesked (ignorér fejl)
    try { await nextBotMessage(page, 15000); } catch {}
    await sleep(800);

    // Send alle spørgsmål i rækkefølge
    // Stop hvis handover er sket – botten svarer ikke efter overdragelse til agent
    let handoverOccurred = false;
    for (let i = 0; i < questions.length; i++) {
      const turn = i + 1;
      const q    = questions[i];
      let botText;

      try {
        botText = await sendAndWait(page, q, config.TIMEOUT_MS);
      } catch (err) {
        botText = `ERROR: ${err.message}`;
      }

      const handover = detectHandover(botText);
      const links    = extractLinks(botText);

      saveConversation(db, sessionId, meta, turn, 'user', q,       false,    []);
      saveConversation(db, sessionId, meta, turn, 'bot',  botText, handover, links);
      results.push({ turn, botText, handover });

      if (handover) { handoverOccurred = true; break; } // stop ved handover
      if (i < questions.length - 1) await sleep(800);
    }

    const anyHandover = results.some(r => r.handover);
    const errors      = results.filter(r => r.botText.startsWith('ERROR:')).length;
    const hoTurn      = anyHandover ? ` [HO turn ${results.find(r => r.handover).turn}]` : '';
    const mark        = errors > 0 ? `✗(${errors} fejl)` : anyHandover ? `✓${hoTurn}` : '✓';
    console.log(`${label} ${mark}`);

  } catch (err) {
    console.log(`${label} ✗ FATAL ${err.message}`);
    // Gem FATAL-fejl for turn 1 hvis ingen svar er gemt endnu
    if (results.length === 0) {
      saveConversation(db, sessionId, meta, 1, 'user', questions[0],          false, []);
      saveConversation(db, sessionId, meta, 1, 'bot',  `ERROR: ${err.message}`, false, []);
    }
  } finally {
    try { await ctx.close(); } catch {}
  }
}

// ─── Main ─────────────────────────────────────────────────────────────────────
async function main() {
  const db = openDb();

  console.log(`\n=== Hiper Cognigy AI Scraper ===`);
  console.log(`Scenarier: ${batch.length} | Parallelitet: ${CONCURRENCY}`);
  console.log(`Endpoint:  ${config.ENDPOINT}\n`);

  const browser   = await chromium.launch({ headless: config.HEADLESS });
  const startTime = Date.now();

  const queue   = batch.map((s, i) => ({ scenario: s, idx: i + 1 }));
  const total   = queue.length;

  async function worker() {
    while (queue.length > 0) {
      const { scenario, idx } = queue.shift();
      const label = `[${String(idx).padStart(2)}/${total}] ${scenario.category.padEnd(22)}`;
      await runScenario(browser, db, scenario, label);
      if (queue.length > 0) {
        await sleep(config.DELAY_MIN + Math.random() * (config.DELAY_MAX - config.DELAY_MIN));
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  await browser.close();

  const elapsed = Math.round((Date.now() - startTime) / 1000);

  // Statistik
  const counts = [1, 2, 3, 4].map(t =>
    db.prepare(`SELECT COUNT(*) as n FROM conversations WHERE turn=? AND role='bot'`).get(t).n
  );
  const errors = db.prepare(`SELECT COUNT(*) as n FROM conversations WHERE role='bot' AND text LIKE 'ERROR%'`).get().n;

  console.log(`\n=== Færdig (${elapsed}s) ===`);
  console.log(`Turn 1: ${counts[0]}  Turn 2: ${counts[1]}  Turn 3: ${counts[2]}  Turn 4: ${counts[3]}`);
  if (errors > 0) console.log(`Fejl: ${errors}`);

  // Link-validering
  await checkLinks.run(db);

  // CSV eksport
  exportCsv(db);
}

// Undgå at unhandled rejections crasher hele processen
process.on('unhandledRejection', (err) => {
  // Stille – fejl håndteres lokalt i runScenario
});

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
