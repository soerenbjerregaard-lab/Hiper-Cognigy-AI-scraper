// Phase 1 – Playwright Layer 1 (parallel)
// Kører alle 49 spørgsmål som single-turn samtaler (ikke-kunde flow)
//
// Flow per samtale:
//   1. Ny browser-context (isoleret session, ingen cookie-deling)
//   2. cognigyWebChat.open() → WS-session startes
//   3. Klik #new_customer i srcdoc-frame
//   4. Vent på velkomstbesked
//   5. sendMessage(spørgsmål) → vent på bot-svar
//   6. Gem i DB
//
// Usage:
//   node phase1_scrape.js              → alle 49, CONCURRENCY=5
//   node phase1_scrape.js --limit 6    → de første 6
//   node phase1_scrape.js --concurrency 8

const { chromium } = require('playwright');
const { randomUUID } = require('crypto');
const { openDb, saveConversation } = require('./db');
const config = require('./config');
const questions = require('./questions.json');

// CLI args
const arg = (flag, def) => {
  const i = process.argv.indexOf(flag);
  return i !== -1 ? parseInt(process.argv[i + 1], 10) : def;
};
const LIMIT       = arg('--limit', questions.length);
const CONCURRENCY = arg('--concurrency', config.CONCURRENCY || 5);
const batch       = questions.slice(0, LIMIT);

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function extractLinks(text) {
  if (!text) return [];
  return [...new Set((text.match(/https?:\/\/[^\s<>"')\]]+/g) || []))];
}

function detectHandover(text) {
  if (!text) return false;
  return config.HANDOVER_TEXT_MARKERS.some(m => text.toLowerCase().includes(m));
}

function waitForBotMessage(page, timeoutMs) {
  return page.evaluate(ms => new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error('timeout')), ms);
    window.cognigyWebChat.onMessage(msg => {
      if (!msg.text || msg.text.trim() === '') return;
      if (msg.data && msg.data._cognigy) return;
      clearTimeout(timer);
      resolve({ text: msg.text, data: msg.data || {} });
    });
  }), timeoutMs);
}

async function runConversation(browser, question) {
  // Isoleret context per samtale – ingen session-deling
  const ctx  = await browser.newContext();
  const page = await ctx.newPage();

  try {
    await page.goto(config.ENDPOINT, { waitUntil: 'networkidle' });
    await sleep(config.PAGE_LOAD_WAIT);

    const welcomePromise = waitForBotMessage(page, 15000);
    await page.evaluate(() => window.cognigyWebChat.open());

    await page.waitForFunction(
      () => document.querySelector('iframe[class*="cognigy-webchat"]') !== null,
      { timeout: 10000 }
    );
    await sleep(1000);

    const srcdocFrame = page.frames().find(f => f.url() === 'about:srcdoc');
    if (!srcdocFrame) throw new Error('srcdoc frame ikke fundet');
    await srcdocFrame.locator('#new_customer').click({ force: true });

    try { await welcomePromise; } catch {}
    await sleep(800);

    let botResponse;
    try {
      const answerPromise = waitForBotMessage(page, config.TIMEOUT_MS);
      await page.evaluate(q => window.cognigyWebChat.sendMessage(q), question.text);
      botResponse = await answerPromise;
    } catch (err) {
      botResponse = { text: `ERROR: ${err.message}`, data: {} };
    }

    return {
      botResponse,
      links:    extractLinks(botResponse.text),
      handover: detectHandover(botResponse.text),
    };
  } finally {
    await ctx.close();
  }
}

async function main() {
  const db = openDb();

  console.log(`\n=== Hiper Cognigy AI Scraper – Phase 1 (parallel) ===`);
  console.log(`Spørgsmål: ${batch.length} | Parallelitet: ${CONCURRENCY}`);
  console.log(`Endpoint:  ${config.ENDPOINT}\n`);

  const browser = await chromium.launch({ headless: config.HEADLESS });

  const startTime = Date.now();
  let successCount = 0;
  let errorCount   = 0;

  // Concurrency pool – kører max CONCURRENCY samtaler parallelt
  const queue   = [...batch];
  const counter = { done: 0 };

  async function worker() {
    while (queue.length > 0) {
      const question  = queue.shift();
      if (!question) break;
      const sessionId = randomUUID();
      const idx       = batch.indexOf(question) + 1;
      const preview   = question.text.slice(0, 50) + (question.text.length > 50 ? '...' : '');

      try {
        const { botResponse, links, handover } = await runConversation(browser, question);
        saveConversation(db, sessionId, question, 1, 'user', question.text, false, []);
        saveConversation(db, sessionId, question, 1, 'bot',  botResponse.text, handover, links);

        const isError = botResponse.text.startsWith('ERROR:');
        const mark    = isError ? '✗' : handover ? '✓ [HO]' : '✓';
        if (isError) errorCount++; else successCount++;

        counter.done++;
        console.log(`[${String(counter.done).padStart(2)}/${batch.length}] ${mark} ${question.category.padEnd(20)} "${preview}"`);
      } catch (err) {
        saveConversation(db, sessionId, question, 1, 'user', question.text,          false, []);
        saveConversation(db, sessionId, question, 1, 'bot',  `ERROR: ${err.message}`, false, []);
        errorCount++;
        counter.done++;
        console.log(`[${String(counter.done).padStart(2)}/${batch.length}] ✗ FATAL ${question.category} – ${err.message.slice(0, 60)}`);
      }

      // Lille delay per worker for ikke at hammere serveren
      await sleep(1000 + Math.random() * 1000);
    }
  }

  // Start N workers parallelt
  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));

  await browser.close();

  const elapsed = Math.round((Date.now() - startTime) / 1000);
  const botRows = db.prepare("SELECT COUNT(*) AS n FROM conversations WHERE role='bot'").get().n;

  console.log(`\n=== Færdig ===`);
  console.log(`Tid: ${elapsed}s | Succes: ${successCount} | Fejl: ${errorCount}`);
  console.log(`DB: ${botRows} bot-svar totalt\n`);
}

main().catch(err => { console.error('Fatal:', err); process.exit(1); });
