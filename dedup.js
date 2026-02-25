const { openDb } = require('./db');
const db = openDb();

const dupes = db.prepare(
  "SELECT text, MIN(session_id) AS keep_sid FROM conversations WHERE role='user' GROUP BY text HAVING COUNT(*) > 1"
).all();

console.log('Rydder', dupes.length, 'duplikerede spørgsmål...');

for (const d of dupes) {
  const sessions = db.prepare(
    "SELECT DISTINCT session_id FROM conversations WHERE role='user' AND text=?"
  ).all(d.text);

  for (const s of sessions) {
    if (s.session_id === d.keep_sid) continue;
    const result = db.prepare('DELETE FROM conversations WHERE session_id=?').run(s.session_id);
    console.log(' Slettet session', s.session_id.slice(0, 8), '(' + result.changes + ' rækker)');
  }
}

const botCount = db.prepare("SELECT COUNT(*) AS n FROM conversations WHERE role='bot'").get().n;
const sessCount = db.prepare('SELECT COUNT(DISTINCT session_id) AS n FROM conversations').get().n;
console.log('\nFærdigt. Bot-svar:', botCount, '| Sessioner:', sessCount);
