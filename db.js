// SQLite helpers for Hiper Cognigy AI Scraper
const Database = require('better-sqlite3');
const config = require('./config');

function openDb() {
  const db = new Database(config.DB_PATH);
  db.pragma('journal_mode = WAL');

  db.exec(`
    CREATE TABLE IF NOT EXISTS conversations (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id   TEXT NOT NULL,
      category     TEXT NOT NULL,
      category_tag TEXT,
      turn         INTEGER NOT NULL,
      role         TEXT NOT NULL,
      text         TEXT NOT NULL,
      handover     INTEGER NOT NULL DEFAULT 0,
      links        TEXT NOT NULL DEFAULT '[]',
      timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_session ON conversations(session_id);
    CREATE INDEX IF NOT EXISTS idx_category ON conversations(category);
  `);

  return db;
}

const insertStmt = (db) => db.prepare(`
  INSERT INTO conversations (session_id, category, category_tag, turn, role, text, handover, links)
  VALUES (@session_id, @category, @category_tag, @turn, @role, @text, @handover, @links)
`);

function saveConversation(db, sessionId, question, turn, role, text, handover = false, links = []) {
  const stmt = insertStmt(db);
  stmt.run({
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
