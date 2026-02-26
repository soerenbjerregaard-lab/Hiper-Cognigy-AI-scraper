'use strict';
// Link-validering: tester alle URLs fra bot-svar
// Markerer døde links (4xx, 5xx, timeout) i conversations.dead_links
//
// Usage (standalone):  node check_links.js
// Importeres også af phase3_followup.js og køres automatisk

const { openDb } = require('./db');

const CONCURRENCY = 5;
const TIMEOUT_MS  = 10000;

async function checkUrl(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      signal:   controller.signal,
      redirect: 'follow',
      headers:  { 'User-Agent': 'Mozilla/5.0 (compatible; HiperLinkChecker/1.0)' },
    });
    clearTimeout(timer);
    return { ok: res.ok, status: res.status };
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, status: err.name === 'AbortError' ? 0 : -1 };
  }
}

async function run(db) {
  // Hent alle unikke URLs fra bot-svar
  const rows = db.prepare(
    "SELECT DISTINCT links FROM conversations WHERE role='bot' AND links != '[]'"
  ).all();

  const allUrls = new Set();
  for (const row of rows) {
    try { JSON.parse(row.links).forEach(u => allUrls.add(u)); } catch {}
  }

  // Filtrer dem der ikke allerede er cachet
  const unchecked = [...allUrls].filter(
    u => !db.prepare('SELECT 1 FROM link_checks WHERE url=?').get(u)
  );

  console.log(`\n=== Link-validering ===`);
  console.log(`${allUrls.size} unikke links | ${unchecked.length} nye skal tjekkes\n`);

  if (unchecked.length > 0) {
    const queue = [...unchecked];
    let done = 0;
    const insertCheck = db.prepare(
      'INSERT OR REPLACE INTO link_checks (url, status_code, ok) VALUES (?, ?, ?)'
    );

    async function worker() {
      while (queue.length > 0) {
        const url = queue.shift();
        const result = await checkUrl(url);
        insertCheck.run(url, result.status, result.ok ? 1 : 0);
        done++;
        const label = result.status === 0 ? 'timeout' : String(result.status);
        console.log(`[${done}/${unchecked.length}] ${result.ok ? '✓' : '✗'} ${label}  ${url}`);
      }
    }

    await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  }

  // Opdater dead_links på alle bot-rækker
  const botRows = db.prepare(
    "SELECT id, links FROM conversations WHERE role='bot'"
  ).all();

  const updateStmt = db.prepare('UPDATE conversations SET dead_links=? WHERE id=?');
  for (const row of botRows) {
    const links = JSON.parse(row.links || '[]');
    const dead  = links.filter(u => {
      const check = db.prepare('SELECT ok FROM link_checks WHERE url=?').get(u);
      return check && !check.ok;
    });
    updateStmt.run(JSON.stringify(dead), row.id);
  }

  // Opsummering
  const totalChecked = db.prepare('SELECT COUNT(*) as n FROM link_checks').get().n;
  const deadCount    = db.prepare('SELECT COUNT(*) as n FROM link_checks WHERE ok=0').get().n;

  console.log(`\nResultat: ${deadCount} døde links ud af ${totalChecked} unikke`);
  if (deadCount > 0) {
    const deadList = db.prepare(
      'SELECT url, status_code FROM link_checks WHERE ok=0 ORDER BY url'
    ).all();
    console.log('Døde links:');
    deadList.forEach(l => {
      const code = l.status_code === 0 ? 'timeout' : l.status_code;
      console.log(`  [${code}]  ${l.url}`);
    });
  }
}

// Standalone kørsel
if (require.main === module) {
  const db = openDb();
  run(db).catch(err => { console.error('Fatal:', err); process.exit(1); });
}

module.exports = { run };
