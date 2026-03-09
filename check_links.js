'use strict';
// Link-validering: tester alle URLs fra bot-svar
// Detekterer både hårde fejl (4xx/5xx/timeout) og soft 404s
// (redirect til forside/generisk hjælpeside)
// Validerer desuden hiper.dk-links mod sitemappet — ét fetch per kørsel
// fanger URL-drift (links der er flyttet men endnu ikke returnerer 404).
//
// Usage (standalone):  node check_links.js
// Importeres også af phase3_followup.js og køres automatisk

const { openDb } = require('./db');

const CONCURRENCY  = 5;
const TIMEOUT_MS   = 10000;
const SITEMAP_URL  = 'https://www.hiper.dk/sitemap.xml';

// Tekstfragmenter der indikerer "siden findes ikke" i HTML-body
const NOT_FOUND_MARKERS = [
  'siden findes ikke', 'page not found', 'ikke fundet',
  '404', 'find ikke siden', 'kunne ikke finde',
];

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

// Detektér content-level soft 404: server returnerer 200 men viser "siden findes ikke"
// To mønstre:
//  1. Siden indeholder kendte "ikke fundet"-fraser i teksten
//  2. SPA-shell: <title> indeholder kun sitenavnet uden side-specifikt indhold
//     (siden er ikke hydreret — JS renderer "ikke fundet" client-side)
function isContentNotFound(html, originalUrl) {
  const lower = html.slice(0, 8000).toLowerCase();

  // Mønster 1: eksplicitte "ikke fundet"-fraser
  if (NOT_FOUND_MARKERS.some(m => lower.includes(m))) return true;

  // Mønster 2: <title> er bare sitenavnet (≤15 tegn) for en URL med dybe stier
  try {
    const urlSegs = new URL(originalUrl).pathname.replace(/\/$/, '').split('/').filter(Boolean).length;
    if (urlSegs >= 2) {
      const titleMatch = html.match(/<title[^>]*>(.*?)<\/title>/i);
      const title = titleMatch ? titleMatch[1].trim() : '';
      if (title.length > 0 && title.length <= 15) return true; // kun sitenavnet, ingen sidebeskrivelse
    }
  } catch {}

  return false;
}

// ── Sitemap-validering ────────────────────────────────────────────────────────

/**
 * Normaliserer en hiper.dk-URL til sitemap-format:
 *  - strip #anchor og ?query
 *  - strip trailing slash (undtagen roddomænet)
 * Returnerer null for URL'er der ikke er på www.hiper.dk.
 */
function normalizeForSitemap(url) {
  try {
    const u = new URL(url);
    if (u.hostname !== 'www.hiper.dk') return null; // subdomæner og eksterne ignoreres
    u.hash   = '';
    u.search = '';
    let str = u.toString();
    // Behold trailing slash kun for rodsiden (/)
    if (str.endsWith('/') && u.pathname !== '/') str = str.slice(0, -1);
    return str;
  } catch { return null; }
}

/** Henter sitemappet og returnerer et Set med normaliserede URL'er. */
async function fetchSitemapUrls() {
  try {
    const res = await fetch(SITEMAP_URL, {
      headers: { 'User-Agent': 'Mozilla/5.0 (compatible; HiperLinkChecker/1.0)' },
    });
    const xml = await res.text();
    const urls = new Set();
    for (const m of xml.matchAll(/<loc>(.*?)<\/loc>/g)) {
      const norm = normalizeForSitemap(m[1].trim());
      if (norm) urls.add(norm);
    }
    console.log(`Sitemap: ${urls.size} kendte URL'er hentet fra ${SITEMAP_URL}`);
    return urls;
  } catch (err) {
    console.warn(`Sitemap-fetch fejlede (${err.message}) — springer sitemap-validering over`);
    return null;  // null = deaktivér sitemap-check for denne kørsel
  }
}

/** Returnerer true for URL'er der skal valideres mod sitemappet (kun www.hiper.dk). */
function isHiperUrl(url) {
  try { return new URL(url).hostname === 'www.hiper.dk'; } catch { return false; }
}

// ── HTTP-validering ───────────────────────────────────────────────────────────

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
    const finalUrl = res.url;
    const redirectDead = isRedirectedAway(url, finalUrl);
    // Læs body for content soft 404 — kun for 200-svar der ikke allerede er flagret
    let contentDead = false;
    if (res.ok && !redirectDead) {
      const html = await res.text();
      contentDead = isContentNotFound(html, url);
    }
    const softDead = redirectDead || contentDead;
    const ok       = res.ok && !softDead;
    return { ok, status: res.status, finalUrl, softDead, contentDead };
  } catch (err) {
    clearTimeout(timer);
    return { ok: false, status: err.name === 'AbortError' ? 0 : -1, finalUrl: url, softDead: false, contentDead: false };
  }
}

async function run(db) {
  // Migrer link_checks-tabellen til at inkludere final_url og redirected
  try { db.exec('ALTER TABLE link_checks ADD COLUMN final_url TEXT'); } catch {}
  try { db.exec('ALTER TABLE link_checks ADD COLUMN redirected INTEGER DEFAULT 0'); } catch {}
  try { db.exec('ALTER TABLE link_checks ADD COLUMN not_in_sitemap INTEGER DEFAULT 0'); } catch {}

  // Re-tjek poster der mangler final_url (cachet før denne opdatering)
  db.exec('DELETE FROM link_checks WHERE final_url IS NULL');

  // Hent sitemappet én gang for hele kørslen
  const sitemapUrls = await fetchSitemapUrls();

  // Opdatér eksisterende cache-entries mod det nye sitemap
  // (fanger URL'er der var OK ved HTTP-check men nu er forsvundet fra sitemappet)
  if (sitemapUrls) {
    const cached = db.prepare("SELECT url FROM link_checks WHERE url LIKE '%hiper.dk%'").all();
    const updateSitemap = db.prepare('UPDATE link_checks SET not_in_sitemap=? WHERE url=?');
    let updatedCount = 0;
    for (const row of cached) {
      const normUrl = normalizeForSitemap(row.url);
      const notIn = normUrl !== null && !sitemapUrls.has(normUrl) ? 1 : 0;
      updateSitemap.run(notIn, row.url);
      if (notIn) updatedCount++;
    }
    // Sæt ok=0 for alle hiper.dk-links der ikke er i sitemappet (uanset HTTP-status)
    db.exec("UPDATE link_checks SET ok=0 WHERE not_in_sitemap=1");
    if (updatedCount > 0) {
      console.log(`Sitemap: ${updatedCount} cached URL'er markeret som ikke-i-sitemap\n`);
    }
  }

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
      'INSERT OR REPLACE INTO link_checks (url, status_code, ok, final_url, redirected, not_in_sitemap) VALUES (?, ?, ?, ?, ?, ?)'
    );

    async function worker() {
      while (queue.length > 0) {
        const url    = queue.shift();
        const result = await checkUrl(url);

        // Sitemap-check: www.hiper.dk-URL er ugyldig hvis den ikke kendes af sitemappet
        const normUrl = normalizeForSitemap(url);
        const notInSitemap = sitemapUrls !== null
          && normUrl !== null
          && !sitemapUrls.has(normUrl)
          ? 1 : 0;

        // En URL er "ok" kun hvis den består HTTP-check OG sitemap-check
        const ok = (result.ok && !notInSitemap) ? 1 : 0;

        insertCheck.run(url, result.status, ok, result.finalUrl, result.softDead ? 1 : 0, notInSitemap);
        done++;

        const icon  = ok ? '✓' : '✗';
        const label = result.status === 0 ? 'timeout' : String(result.status);
        const note  = notInSitemap        ? ' [ikke i sitemap]'
                    : result.contentDead  ? ' [content: ikke fundet]'
                    : result.softDead     ? ` [redirect → ${result.finalUrl}]`
                    : '';
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
  const totalChecked      = db.prepare('SELECT COUNT(*) as n FROM link_checks').get().n;
  const deadCount         = db.prepare('SELECT COUNT(*) as n FROM link_checks WHERE ok=0').get().n;
  const sitemapDeadCount  = db.prepare('SELECT COUNT(*) as n FROM link_checks WHERE not_in_sitemap=1').get().n;
  const redirectCount     = db.prepare('SELECT COUNT(*) as n FROM link_checks WHERE redirected=1 AND not_in_sitemap=0').get().n;
  const hardDeadCount     = deadCount - sitemapDeadCount - redirectCount;

  console.log(`\nResultat: ${deadCount} problematiske links ud af ${totalChecked} unikke`);
  if (sitemapDeadCount > 0) console.log(`  Ikke i sitemap (URL-drift):             ${sitemapDeadCount}`);
  if (redirectCount    > 0) console.log(`  Soft 404 (redirect til generisk side):  ${redirectCount}`);
  if (hardDeadCount    > 0) console.log(`  Hård fejl (4xx/5xx/timeout):            ${hardDeadCount}`);

  if (deadCount > 0) {
    const deadList = db.prepare(
      `SELECT url, status_code, redirected, not_in_sitemap, final_url
       FROM link_checks WHERE ok=0
       ORDER BY not_in_sitemap DESC, redirected DESC, url`
    ).all();
    console.log('\nProblematiske links:');
    deadList.forEach(l => {
      const code  = l.status_code === 0 ? 'timeout' : l.status_code;
      const type  = l.not_in_sitemap ? 'ikke-i-sitemap' : l.redirected ? 'soft-404' : `HTTP ${code}`;
      const extra = l.redirected && !l.not_in_sitemap ? ` → ${l.final_url}` : '';
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
