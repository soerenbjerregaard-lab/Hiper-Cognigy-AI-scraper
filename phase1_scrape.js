// Phase 1 – Playwright Layer 1
// Kører alle 49 spørgsmål som single-turn samtaler (ikke-kunde flow)
// Usage: node phase1_scrape.js [--limit N]

const { chromium } = require('playwright');
const { randomUUID } = require('crypto');
const { openDb, saveConversation } = require('./db');
const config = require('./config');
const questions = require('./questions.json');

// Parse --limit argument
const limitArg = process.argv.indexOf('--limit');
const LIMIT = limitArg !== -1 ? parseInt(process.argv[limitArg + 1], 10) : questions.length;
const batch = questions.slice(0, LIMIT);

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function extractLinks(text) {
  if (!text) return [];
  const urlRegex = /https?:\/\/[^\s<>"')\]]+/g;
  return [...new Set(text.match(urlRegex) || [])];
}

function detectHandover(text, data) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return config.HANDOVER_TEXT_MARKERS.some((m) => lower.includes(m));
}

async function runConversation(page, question, sessionId) {
  // Naviger til chat-endpoint for ny session
  await page.goto(config.ENDPOINT, { waitUntil: 'networkidle' });
  await sleep(config.PAGE_LOAD_WAIT);

  // Klik "Jeg er ikke kunde" via koordinat
  if (config.IKKE_KUNDE_X === null || config.IKKE_KUNDE_Y === null) {
    throw new Error(
      'IKKE_KUNDE_X/Y er ikke konfigureret i config.js. Kør measure_coords.js først.'
    );
  }
  await page.mouse.click(config.IKKE_KUNDE_X, config.IKKE_KUNDE_Y);
  await sleep(config.ONBOARDING_WAIT);

  // Inject listener og send spørgsmål
  let botResponse;
  try {
    botResponse = await page.evaluate(
      ({ q, timeoutMs }) => {
        return new Promise((resolve, reject) => {
          const timer = setTimeout(
            () => reject(new Error('timeout')),
            timeoutMs
          );

          window.cognigyWebChat.onMessage((msg) => {
            // Skip den altid-første handover_available:true besked
            if (msg.data && msg.data.handover_available === true) return;
            clearTimeout(timer);
            resolve({ text: msg.text || '', data: msg.data || {} });
          });

          window.cognigyWebChat.sendMessage(q);
        });
      },
      { q: question.text, timeoutMs: config.TIMEOUT_MS }
    );
  } catch (err) {
    botResponse = { text: `ERROR: ${err.message}`, data: {} };
  }

  const links = extractLinks(botResponse.text);
  const handover = detectHandover(botResponse.text, botResponse.data);

  return { botResponse, links, handover };
}

async function main() {
  const db = openDb();

  console.log(`\n=== Hiper Cognigy AI Scraper – Phase 1 ===`);
  console.log(`Kører ${batch.length} af ${questions.length} spørgsmål\n`);

  const browser = await chromium.launch({ headless: config.HEADLESS });

  for (let i = 0; i < batch.length; i++) {
    const question = batch[i];
    const sessionId = randomUUID();
    const label = `[${i + 1}/${batch.length}] ${question.category}: "${question.text.slice(0, 60)}..."`;

    process.stdout.write(label);

    try {
      const page = await browser.newPage();
      const { botResponse, links, handover } = await runConversation(page, question, sessionId);
      await page.close();

      // Gem user-turn
      saveConversation(db, sessionId, question, 1, 'user', question.text, false, []);

      // Gem bot-turn
      saveConversation(db, sessionId, question, 1, 'bot', botResponse.text, handover, links);

      const handoverMark = handover ? ' [HANDOVER]' : '';
      const errorMark = botResponse.text.startsWith('ERROR:') ? ' [FEJL]' : '';
      console.log(` ✓${handoverMark}${errorMark}`);
    } catch (err) {
      console.log(` ✗ FATAL: ${err.message}`);
      // Gem fejl i DB så session ikke mangler
      saveConversation(db, sessionId, question, 1, 'user', question.text, false, []);
      saveConversation(db, sessionId, question, 1, 'bot', `ERROR: ${err.message}`, false, []);
    }

    // Random delay mellem samtaler (undgå rate limiting)
    if (i < batch.length - 1) {
      const delay = config.DELAY_MIN + Math.random() * (config.DELAY_MAX - config.DELAY_MIN);
      await sleep(delay);
    }
  }

  await browser.close();

  const rowCount = db
    .prepare('SELECT COUNT(*) as n FROM conversations WHERE turn = 1')
    .get().n;

  console.log(`\n=== Færdig ===`);
  console.log(`DB indeholder ${rowCount} rækker (${rowCount / 2} samtaler)\n`);
}

main().catch((err) => {
  console.error('Fatal error:', err);
  process.exit(1);
});
