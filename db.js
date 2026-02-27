// SQLite helpers for Hiper Cognigy AI Scraper
// Bruger node:sqlite (built-in i Node 22+, ingen native build nødvendig)
const { DatabaseSync } = require('node:sqlite');
const config = require('./config');

// Suppress experimental warning
process.removeAllListeners('warning');

function openDb() {
  const db = new DatabaseSync(config.DB_PATH);
  db.exec('PRAGMA journal_mode = WAL');

  db.exec(`
    CREATE TABLE IF NOT EXISTS conversations (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id       TEXT,
      endpoint     TEXT,
      session_id   TEXT NOT NULL,
      category     TEXT NOT NULL,
      category_tag TEXT,
      turn         INTEGER NOT NULL,
      role         TEXT NOT NULL,
      text         TEXT NOT NULL,
      handover     INTEGER NOT NULL DEFAULT 0,
      links        TEXT NOT NULL DEFAULT '[]',
      dead_links   TEXT NOT NULL DEFAULT '[]',
      timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS link_checks (
      url          TEXT PRIMARY KEY,
      status_code  INTEGER,
      ok           INTEGER DEFAULT 0,
      checked_at   DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id);
    CREATE INDEX IF NOT EXISTS idx_category ON conversations(category);
  `);

  // Migrer eksisterende DB'er der mangler de nye kolonner/tabeller
  try { db.exec('ALTER TABLE conversations ADD COLUMN dead_links TEXT NOT NULL DEFAULT "[]"'); } catch {}
  try { db.exec('ALTER TABLE conversations ADD COLUMN run_id TEXT'); } catch {}
  try { db.exec('ALTER TABLE conversations ADD COLUMN endpoint TEXT'); } catch {}

  return db;
}

const insertStmt = (db) => db.prepare(`
  INSERT INTO conversations (run_id, endpoint, session_id, category, category_tag, turn, role, text, handover, links)
  VALUES (@run_id, @endpoint, @session_id, @category, @category_tag, @turn, @role, @text, @handover, @links)
`);

function saveConversation(db, sessionId, question, turn, role, text, handover = false, links = [], runId = null, endpoint = null) {
  const stmt = insertStmt(db);
  stmt.run({
    run_id:       runId,
    endpoint:     endpoint,
    session_id:   sessionId,
    category:     question.category,
    category_tag: question.category_tag || null,
    turn,
    role,
    text,
    handover:     handover ? 1 : 0,
    links:        JSON.stringify(links),
  });
}

function getAllSessions(db) {
  return db.prepare(`
    SELECT
      session_id,
      category,
      category_tag,
      MAX(CASE WHEN role = 'user' AND turn = 1 THEN text END) AS question,
      MAX(CASE WHEN role = 'bot'  AND turn = 1 THEN text END) AS bot_answer,
      MAX(CASE WHEN role = 'bot'  AND turn = 1 THEN handover END) AS handover
    FROM conversations
    GROUP BY session_id
    ORDER BY session_id
  `).all();
}

function getFullThread(db, sessionId) {
  return db.prepare(`
    SELECT turn, role, text, handover, links
    FROM conversations
    WHERE session_id = ?
    ORDER BY turn, role DESC
  `).all(sessionId);
}

module.exports = { openDb, saveConversation, getAllSessions, getFullThread };
