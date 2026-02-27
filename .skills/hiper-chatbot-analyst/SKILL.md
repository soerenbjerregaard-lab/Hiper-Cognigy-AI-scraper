---
name: hiper-chatbot-analyst
description: "Hiper Cognigy AI chatbot quality analysis skill. Provides context for querying the conversations.db SQLite database on the Lenovo server via SSH. Use when analyzing chatbot performance for: (1) category deep-dive analysis (resolution scores, weak spots per topic), (2) link & hallucination audits (dead links, kb_gaps, hallucination_risk tracking), (3) multi-turn context retention analysis (score degradation across turns, context_retention patterns), or any data questions about Hiper's chatbot test results."
---

# Hiper Chatbot Quality Analysis

## Database Access

The primary database lives on the Lenovo server. Access via SSH through Tailscale:

- **Host**: `100.124.174.76`
- **User**: `soren`
- **DB path on server**: `/home/soren/Hiper-Cognigy-AI-scraper/conversations.db`
- **DB type**: SQLite 3

To query the database, use the `ssh-remote` MCP tool or the `remote-ssh` tool with:
```bash
sqlite3 /home/soren/Hiper-Cognigy-AI-scraper/conversations.db "<SQL_QUERY>"
```

For formatted output:
```bash
sqlite3 -header -column /home/soren/Hiper-Cognigy-AI-scraper/conversations.db "<SQL_QUERY>"
```

For CSV output:
```bash
sqlite3 -header -csv /home/soren/Hiper-Cognigy-AI-scraper/conversations.db "<SQL_QUERY>"
```

---

## SQL Dialect: SQLite

- **Table references**: Plain names, no quoting needed unless reserved words
- **Safe division**: `NULLIF(b, 0)` pattern: `a / NULLIF(b, 0)` — returns NULL on divide-by-zero
- **Date functions**:
  - `DATE(timestamp_col)` to extract date
  - `STRFTIME('%Y-%m', timestamp)` for month truncation
  - `DATETIME('now', '-7 days')` for relative dates
- **JSON**: `JSON_EXTRACT(col, '$.field')` or `col->>'$.field'` (SQLite 3.38+)
- **String matching**: `LIKE` (case-insensitive by default), `GLOB` (case-sensitive)
- **Boolean**: Stored as INTEGER (0/1), no native BOOLEAN
- **NULLs**: Use `COALESCE()` or `IFNULL()`
- **Group concat**: `GROUP_CONCAT(col, separator)` for string aggregation
- **No window functions limit**: SQLite supports `ROW_NUMBER()`, `LAG()`, `LEAD()` etc.

---

## Entity Disambiguation

### "Session" / "Samtale"
A single test conversation with the Cognigy chatbot. Identified by `session_id` (UUID). Each session belongs to one `category` and optionally a `category_tag`. A session contains multiple turns.

### "Turn"
One exchange within a session. Each turn has a `user` message and a `bot` response. Turn 1 is the initial question (from `scenarios.json`), turns 2+ are follow-ups (from `followups.json`).

### "Handover"
When the bot escalates to a human agent. Detected by text markers (e.g. "sat i kø", "viderestiller", "kollega"). Stored as `handover` INTEGER (0/1) on bot messages.

### "Category"
The topic classification of each test scenario:

| Category | Beskrivelse | category_tag |
|----------|-------------|--------------|
| **SBBU** | Skifte-Bestil-Bestilling-Udbyder (salgsrelateret) | `SALES_HANDOVER_EXPECTED` |
| **Etablering** | Fiberboks, teknikerbesøg, ny installation | `null` |
| **Flytning/overdragelse** | Flytning af abonnement, adresseændring | `null` |
| **Hastighed** | Hastighedsproblemer, speedtest, langsomt net | `null` |
| **Regning** | Fakturering, betaling, PBS | `null` |
| **Ustabil** | Ustabil forbindelse, udfald, packet loss | `null` |
| **Udstyr** | Router, WiFi, hardware | `null` |
| **Offline** | Internet nede, ingen forbindelse | `null` |
| **Support øvrige** | Diverse supportemner | `null` |
| **Øvrige** | Alt andet (produktskifte, streaming osv.) | `null` |

### "Endpoint"
The Cognigy AI configuration being tested. Different endpoints use different AI models:
- `gpt41`: GPT-4.1 endpoint (`https://cognigy-assets.hiper.dk/x-scraping-new-prompt-gpt4-1/`)
- `gpt5`: GPT-5 endpoint (`https://cognigy-assets.hiper.dk/x-scraping-gpt5-endpoint/`)

**Note**: Endpoint is NOT stored in the database. Different test runs against different endpoints produce separate DB files or sessions. Track by run timestamp or separate exports.

---

## Business Terminology

| Term | Definition | Notes |
|------|------------|-------|
| Resolution score | 0-5 score for how well the bot solved the customer's problem | 0=ingen hjælp, 5=fuldstændig løsning |
| Context retention | 0-5 score for how well the bot maintains context across turns | Only relevant for multi-turn sessions |
| Handover justified | Whether escalation to human was appropriate | For SBBU: handover is always expected/justified |
| kb_gap | Knowledge base gap — what the bot lacked knowledge about | Free text, null if no gap |
| Hallucination risk | Bot invented factual details that can't be verified | Boolean |
| Dead link | A URL in the bot's response that returns HTTP error | Verified by `check_links.js` |
| Multi-turn | Session with 2+ turns (follow-up questions) | ~54 of 103 sessions typically |
| Single-turn | Session with only 1 turn (initial question only) | ~49 of 103 sessions typically |

---

## Standard Filters

Always apply unless explicitly told otherwise:

```sql
-- No standard exclusions needed — all data is test data by design.
-- However, watch for these patterns:

-- Empty bot responses (known scraper bug in some runs)
WHERE text != '' AND text IS NOT NULL

-- Filter by role
AND role = 'bot'   -- for bot analysis
AND role = 'user'  -- for user questions
```

**When analyzing handovers for SBBU category:**
```sql
-- SBBU has category_tag = 'SALES_HANDOVER_EXPECTED'
-- Handover is EXPECTED here — don't flag as problem
WHERE category_tag = 'SALES_HANDOVER_EXPECTED'
```

---

## Key Metrics

### Resolution Score (resolution_score)
- **Definition**: How completely the bot solved the customer's issue (0-5)
- **Formula**: Manually scored per session by Claude evaluation
- **Source**: `evaluations.resolution_score` (planned) or rapport files
- **Benchmark**: Current average 3.23/5 (v2 rapport)

### Context Retention (context_retention)
- **Definition**: How well the bot remembers context from earlier turns (0-5)
- **Formula**: Manually scored per multi-turn session
- **Source**: `evaluations.context_retention` (planned) or rapport files
- **Benchmark**: Current average 3.19/5 (v2 rapport, multi-turn only)

### Handover Rate
- **Definition**: Percentage of sessions where bot triggered handover
- **Formula**: `COUNT(CASE WHEN handover=1) / COUNT(DISTINCT session_id)`
- **Source**: `conversations` table, `handover` column on bot messages
- **Caveat**: Split by justified vs. unjustified for meaningful analysis

### Dead Link Rate
- **Definition**: Percentage of bot responses containing broken links
- **Formula**: Links extracted during scraping, verified by `check_links.js`
- **Source**: `conversations.links` (JSON array), `conversations.dead_links` (JSON array), `link_checks` table

---

## Data Freshness

| Table | Update Frequency | Notes |
|-------|------------------|-------|
| `conversations` | Per test run (manual) | New rows added each run. ~100-200 rows per full run |
| `link_checks` | Per link check run | Run separately via `check_links.js` |
| `evaluations` | Planned — not yet in DB | Currently in rapport markdown files |

To check latest data:
```sql
SELECT MAX(timestamp) as latest, COUNT(*) as total_rows,
       COUNT(DISTINCT session_id) as sessions
FROM conversations;
```

---

## Knowledge Base Navigation

| Domain | Reference File | Use For |
|--------|----------------|---------|
| Conversations | `references/conversations.md` | Main table: sessions, turns, messages, handovers |
| Links | `references/links.md` | Link verification, dead link tracking |
| Evaluations | `references/evaluations.md` | Quality scores, planned DB schema |
| Metrics | `references/metrics.md` | KPI calculations and formulas |

---

## Common Query Patterns

### Sessions per category
```sql
SELECT category, category_tag,
       COUNT(DISTINCT session_id) as sessions,
       COUNT(*) as total_messages
FROM conversations
GROUP BY category, category_tag
ORDER BY sessions DESC;
```

### Handover analysis per category
```sql
SELECT category,
       COUNT(DISTINCT session_id) as total_sessions,
       COUNT(DISTINCT CASE WHEN handover = 1 THEN session_id END) as handover_sessions,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN handover = 1 THEN session_id END) /
             COUNT(DISTINCT session_id), 1) as handover_pct
FROM conversations
WHERE role = 'bot'
GROUP BY category
ORDER BY handover_pct DESC;
```

### Full conversation thread for a session
```sql
SELECT turn, role, text, handover,
       JSON_EXTRACT(links, '$') as links
FROM conversations
WHERE session_id = ?
ORDER BY turn, CASE role WHEN 'user' THEN 0 ELSE 1 END;
```

### Sessions with dead links
```sql
SELECT session_id, category, turn, text,
       dead_links
FROM conversations
WHERE dead_links != '[]' AND dead_links != ''
ORDER BY category, session_id;
```

### Multi-turn vs single-turn session counts
```sql
SELECT category,
       COUNT(DISTINCT CASE WHEN max_turn = 1 THEN session_id END) as single_turn,
       COUNT(DISTINCT CASE WHEN max_turn > 1 THEN session_id END) as multi_turn
FROM (
    SELECT session_id, category, MAX(turn) as max_turn
    FROM conversations
    GROUP BY session_id, category
) sub
GROUP BY category;
```

### Bot responses with empty text (known bug)
```sql
SELECT session_id, category, turn
FROM conversations
WHERE role = 'bot' AND (text = '' OR text IS NULL)
ORDER BY category, session_id, turn;
```

---

## Planned: Evaluations Table

The project currently stores evaluation data in markdown reports. The plan is to add an `evaluations` table to the database:

```sql
CREATE TABLE IF NOT EXISTS evaluations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT NOT NULL,
    category           TEXT NOT NULL,
    category_tag       TEXT,
    resolution_score   INTEGER CHECK(resolution_score BETWEEN 0 AND 5),
    context_retention  INTEGER CHECK(context_retention BETWEEN 0 AND 5),
    handover_triggered INTEGER NOT NULL DEFAULT 0,
    handover_justified INTEGER,  -- NULL if no handover
    dead_links         TEXT NOT NULL DEFAULT '[]',  -- JSON array
    kb_gap             TEXT,
    hallucination_risk INTEGER NOT NULL DEFAULT 0,
    notes              TEXT,
    endpoint           TEXT,     -- 'gpt41', 'gpt5', etc.
    run_timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
);

CREATE INDEX IF NOT EXISTS idx_eval_session ON evaluations(session_id);
CREATE INDEX IF NOT EXISTS idx_eval_category ON evaluations(category);
CREATE INDEX IF NOT EXISTS idx_eval_endpoint ON evaluations(endpoint);
```

---

## Troubleshooting

### Common Mistakes
- **Forgetting role filter**: Conversations table has both `user` and `bot` rows. Always filter by `role` when counting handovers (only on bot messages) or analyzing bot quality.
- **JSON columns are strings**: `links` and `dead_links` are JSON arrays stored as TEXT. Use `JSON_EXTRACT()` or string matching, not direct comparison.
- **Turn ordering**: Use `ORDER BY turn, CASE role WHEN 'user' THEN 0 ELSE 1 END` to get correct user→bot ordering within each turn.
- **SBBU handovers are expected**: Don't count SBBU handovers as failures — `category_tag = 'SALES_HANDOVER_EXPECTED'` means handover is the correct behavior.

### Performance Tips
- Database is small (~500 rows per run) — no performance concerns
- Use `COUNT(DISTINCT session_id)` not `COUNT(*)` when counting sessions
- Filter by `category` first when exploring specific topics
