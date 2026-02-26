'use strict';
// Link-validering: tester alle URLs fra bot-svar
// Detekterer både hårde fejl (4xx/5xx/timeout) og soft 404s
// (redirect til forside/generisk hjælpeside)
//
// Usage (standalone):  node check_links.js
// Importeres også af phase3_followup.js og køres automatisk

const { openDb } = require('./db');

const CONCURRENCY = 5;
const TIMEOUT_MS  = 10000;

// Detektér soft 404: URL redirectede til en markant kortere/anden sti
// Eks: /hjaelp/artikel/specifik  →  /hjaelp  = soft 404
function isRedirectedAway(originalUrl, finalUrl) {
  if (originalUrl === finalUrl) return false;
  try {
    const orig  = new URL(originalUrl);
    const final = new URL(finalUrl);
    if (orig.hostname !== final.hostname) return true; // andet domæne
    const origSegs  = orig.pathname.replace(/\/$/, '').split('/').filter(Boolean).length;
    const finalSegs = final.pathname.replace(/\/$/, '').split('/').filter(Boolean).length;
    // Fx 4 segmenter → 1 segment = redirectet til catchall-side
    return origSegs >= 2 && finalSegs < origSegs - 1;
  } catch { return false; }
}

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
    const finalUrl   = res.url;
    const softDead   = isRedirectedAway(url, finalUrl);
    const ok         = res.ok && !softDead;
    return { ok, status: res.status, finalUrl, softDead };
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, status: err.name === 'AbortError' ? 0 : -1, finalUrl: url, softDead: false };
  }
}

async function run(db) {
  // Migrer link_checks-tabellen til at inkludere final_url og redirected
  try { db.exec('ALTER TABLE link_checks ADD COLUMN final_url TEXT'); } catch {}
  try { db.exec('ALTER TABLE link_checks ADD COLUMN redirected INTEGER DEFAULT 0'); } catch {}

  // Re-tjek poster der mangler final_url (cachet før denne opdatering)
  db.exec('DELETE FROM link_checks WHERE final_url IS NULL');

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
  console.log(`${allUrls.size} unikke links | ${unchecked.length} skal tjekkes\n`);

  if (unchecked.length > 0) {
    const queue = [...unchecked];
    let done = 0;
    const insertCheck = db.prepare(
      'INSERT OR REPLACE INTO link_checks (url, status_code, ok, final_url, redirected) VALUES (?, ?, ?, ?, ?)'
    );

    async function worker() {
      while (queue.length > 0) {
        const url    = queue.shift();
        const result = await checkUrl(url);
        insertCheck.run(url, result.status, result.ok ? 1 : 0, result.finalUrl, result.softDead ? 1 : 0);
        done++;
        const icon  = result.ok ? '✓' : '✗';
        const label = result.status === 0 ? 'timeout' : String(result.status);
        const note  = result.softDead ? ` → redirect: ${result.finalUrl}` : '';
        console.log(`[${done}/${unchecked.length}] ${icon} ${label}${note}  ${url}`);
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
  const totalChecked   = db.prepare('SELECT COUNT(*) as n FROM link_checks').get().n;
  const deadCount      = db.prepare('SELECT COUNT(*) as n FROM link_checks WHERE ok=0').get().n;
  const redirectCount  = db.prepare('SELECT COUNT(*) as n FROM link_checks WHERE redirected=1').get().n;
  const hardDeadCount  = deadCount - redirectCount;

  console.log(`\nResultat: ${deadCount} problematiske links ud af ${totalChecked} unikke`);
  if (redirectCount > 0) console.log(`  Soft 404 (redirect til generisk side): ${redirectCount}`);
  if (hardDeadCount > 0) console.log(`  Hård fejl (4xx/5xx/timeout):           ${hardDeadCount}`);

  if (deadCount > 0) {
    const deadList = db.prepare(
      'SELECT url, status_code, redirected, final_url FROM link_checks WHERE ok=0 ORDER BY redirected DESC, url'
    ).all();
    console.log('\nProblematiske links:');
    deadList.forEach(l => {
      const code = l.status_code === 0 ? 'timeout' : l.status_code;
      const type = l.redirected ? 'soft-404' : `HTTP ${code}`;
      const extra = l.redirected ? ` → ${l.final_url}` : '';
      console.log(`  [${type}]  ${l.url}${extra}`);
    });
  }
}

// Standalone kørsel
if (require.main === module) {
  const db = openDb();
  run(db).catch(err => { console.error('Fatal:', err); process.exit(1); });
}

module.exports = { run };
