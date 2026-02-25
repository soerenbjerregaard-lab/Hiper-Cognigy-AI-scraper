// Phase 3 – Playwright Layer 2 + 3
// Genoptager sessioner fra Phase 1 og sender opfølgningsspørgsmål (turn 2 og 3)
//
// Session-genoptagelse: bruger cognigyWebChat.setCognigySessionId() (Option B)
// Hvis det ikke virker med Cognigy: skift RESUME_MODE til 'option-a' og
// kør phase1 + phase3 i ét sammenhængende script.
//
// Usage: node phase3_followup.js [--limit N]

const { chromium } = require('playwright');
const { openDb, saveConversation } = require('./db');
const config = require('./config');
const fs = require('fs');
const path = require('path');

const FOLLOWUPS_PATH = path.join(__dirname, 'followups.json');

// Parse --limit argument
const limitArg = process.argv.indexOf('--limit');

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function extractLinks(text) {
  if (!text) return [];
  const urlRegex = /https?:\/\/[^\s<>"')\]]+/g;
  return [...new Set(text.match(urlRegex) || [])];
}

function detectHandover(text) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return config.HANDOVER_TEXT_MARKERS.some((m) => lower.includes(m));
}

async function resumeSession(page, sessionId) {
  await page.goto(config.ENDPOINT, { waitUntil: 'networkidle' });
  await sleep(config.PAGE_LOAD_WAIT);

  // Option B: Forsøg at genoptage session via Cognigy API
  const resumed = await page.evaluate((sid) => {
    try {
      if (typeof window.cognigyWebChat?.setCognigySessionId === 'function') {
        window.cognigyWebChat.setCognigySessionId(sid);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }, sessionId);

  if (!resumed) {
    // Fallback: klik "ikke-kunde" flow som i Phase 1
    console.warn(`  [WARN] setCognigySessionId ikke tilgængelig – bruger ny session`);
    if (config.IKKE_KUNDE_X !== null) {
      await page.mouse.click(config.IKKE_KUNDE_X, config.IKKE_KUNDE_Y);
      await sleep(config.ONBOARDING_WAIT);
    }
  }

  return resumed;
}

async function sendTurn(page, question, timeoutMs) {
  try {
    return await page.evaluate(
      ({ q, timeoutMs }) => {
        return new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('timeout')), timeoutMs);
          window.cognigyWebChat.onMessage((msg) => {
            if (msg.data && msg.data.handover_available === true) return;
            clearTimeout(timer);
            resolve({ text: msg.text || '', data: msg.data || {} });
          });
          window.cognigyWebChat.sendMessage(q);
        });
      },
      { q: question, timeoutMs }
    );
  } catch (err) {
    return { text: `ERROR: ${err.message}`, data: {} };
  }
}

async function main() {
  if (!fs.existsSync(FOLLOWUPS_PATH)) {
    console.error(`FEJL: followups.json ikke fundet. Kør phase2_generate.py og gem output som followups.json.`);
    process.exit(1);
  }

  const followups = JSON.parse(fs.readFileSync(FOLLOWUPS_PATH, 'utf8'));
  const db = openDb();

  const limitVal = limitArg !== -1 ? parseInt(process.argv[limitArg + 1], 10) : followups.length;
  const batch = followups.slice(0, limitVal);

  console.log(`\n=== Hiper Cognigy AI Scraper – Phase 3 ===`);
  console.log(`Kører opfølgninger for ${batch.length} sessioner\n`);

  const browser = await chromium.launch({ headless: config.HEADLESS });

  for (let i = 0; i < batch.length; i++) {
    const entry = batch[i];
    const { session_id, category, category_tag, original_question, followup_1, followup_2 } = entry;

    // Byg question-objekt kompatibelt med saveConversation
    const questionMeta = { category, category_tag: category_tag || null };

    const label = `[${i + 1}/${batch.length}] ${category}: "${(followup_1 || '').slice(0, 50)}..."`;
    process.stdout.write(label);

    try {
      const page = await browser.newPage();
      await resumeSession(page, session_id);

      // Turn 2
      const resp2 = await sendTurn(page, followup_1, config.TIMEOUT_MS);
      const links2 = extractLinks(resp2.text);
      const handover2 = detectHandover(resp2.text);
      saveConversation(db, session_id, questionMeta, 2, 'user', followup_1, false, []);
      saveConversation(db, session_id, questionMeta, 2, 'bot', resp2.text, handover2, links2);

      await sleep(1500);

      // Turn 3
      const resp3 = await sendTurn(page, followup_2, config.TIMEOUT_MS);
      const links3 = extractLinks(resp3.text);
      const handover3 = detectHandover(resp3.text);
      saveConversation(db, session_id, questionMeta, 3, 'user', followup_2, false, []);
      saveConversation(db, session_id, questionMeta, 3, 'bot', resp3.text, handover3, links3);

      await page.close();

      const h = (handover2 || handover3) ? ' [HANDOVER]' : '';
      console.log(` ✓${h}`);
    } catch (err) {
      console.log(` ✗ FATAL: ${err.message}`);
    }

    // Delay mellem sessioner
    if (i < batch.length - 1) {
      const delay = config.DELAY_MIN + Math.random() * (config.DELAY_MAX - config.DELAY_MIN);
      await sleep(delay);
    }
  }

  await browser.close();

  const rowCount = db
    .prepare('SELECT COUNT(*) as n FROM conversations WHERE turn IN (2,3) AND role = "bot"')
    .get().n;

  console.log(`\n=== Færdig ===`);
  console.log(`${rowCount} opfølgningssvar gemt i DB\n`);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
