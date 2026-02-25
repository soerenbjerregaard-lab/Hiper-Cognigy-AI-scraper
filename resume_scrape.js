// Kører kun spørgsmål der ikke allerede er i DB
// Usage: node resume_scrape.js

const { chromium } = require('playwright');
const { randomUUID } = require('crypto');
const { openDb, saveConversation } = require('./db');
const config = require('./config');
const questions = require('./questions.json');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function extractLinks(text) {
  if (!text) return [];
  return [...new Set((text.match(/https?:\/\/[^\s<>"')\]]+/g) || []))];
}

function detectHandover(text) {
  if (!text) return false;
  const lower = text.toLowerCase();
  return config.HANDOVER_TEXT_MARKERS.some(m => lower.includes(m));
}

function waitForBotMessage(page, timeoutMs) {
  return page.evaluate((timeoutMs) => {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('timeout')), timeoutMs);
      window.cognigyWebChat.onMessage((msg) => {
        if (!msg.text || msg.text.trim() === '') return;
        if (msg.data && msg.data._cognigy) return;
        clearTimeout(timer);
        resolve({ text: msg.text, data: msg.data || {} });
      });
    });
  }, timeoutMs);
}

async function runConversation(page, question) {
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
    links: extractLinks(botResponse.text),
    handover: detectHandover(botResponse.text),
  };
}

async function main() {
  const db = openDb();

  // Find spørgsmål der ikke er i DB
  const doneTexts = new Set(
    db.prepare("SELECT text FROM conversations WHERE role='user'").all().map(r => r.text)
  );
  const remaining = questions.filter(q => !doneTexts.has(q.text));

  if (remaining.length === 0) {
    console.log('Alle 49 spørgsmål er allerede i DB. Intet at gøre.');
    return;
  }

  console.log(`\n=== Resume Scrape ===`);
  console.log(`${doneTexts.size} allerede i DB – kører de resterende ${remaining.length}\n`);

  const browser = await chromium.launch({ headless: config.HEADLESS });
  let success = 0, errors = 0;

  for (let i = 0; i < remaining.length; i++) {
    const question = remaining[i];
    const sessionId = randomUUID();
    const preview = question.text.slice(0, 55) + (question.text.length > 55 ? '...' : '');

    process.stdout.write(
      `[${String(i + 1).padStart(2)}/${remaining.length}] ${question.category.padEnd(22)} "${preview}"`
    );

    try {
      const page = await browser.newPage();
      const { botResponse, links, handover } = await runConversation(page, question);
      await page.close();

      saveConversation(db, sessionId, question, 1, 'user', question.text, false, []);
      saveConversation(db, sessionId, question, 1, 'bot', botResponse.text, handover, links);

      const isError = botResponse.text.startsWith('ERROR:');
      console.log(isError ? ' ✗ [FEJL]' : handover ? ' ✓ [HANDOVER]' : ' ✓');
      if (isError) errors++; else success++;
    } catch (err) {
      console.log(` ✗ FATAL: ${err.message}`);
      saveConversation(db, sessionId, question, 1, 'user', question.text, false, []);
      saveConversation(db, sessionId, question, 1, 'bot', `ERROR: ${err.message}`, false, []);
      errors++;
    }

    if (i < remaining.length - 1) {
      const delay = config.DELAY_MIN + Math.random() * (config.DELAY_MAX - config.DELAY_MIN);
      await sleep(delay);
    }
  }

  await browser.close();

  const total = db.prepare("SELECT COUNT(*) AS n FROM conversations WHERE role='bot'").get().n;
  console.log(`\n=== Færdig ===`);
  console.log(`Succes: ${success} | Fejl: ${errors}`);
  console.log(`DB total: ${total} bot-svar\n`);
}

main().catch(err => { console.error(err); process.exit(1); });
