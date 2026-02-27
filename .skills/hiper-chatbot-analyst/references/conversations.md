# Conversations Table

The core table storing all chatbot test interactions.

---

## Quick Reference

### Business Context
Each row is a single message in a test conversation with Hiper's Cognigy AI chatbot. Conversations are grouped by `session_id` and ordered by `turn`. The bot is tested with pre-defined scenarios across 10 categories covering common customer support topics for the ISP Hiper.

### Standard Filters
```sql
-- Always filter by role when analyzing one side
WHERE role = 'bot'    -- bot responses only
WHERE role = 'user'   -- customer questions only

-- Exclude empty responses (known scraper bug)
AND text != '' AND text IS NOT NULL
```

---

## Table: conversations

**Location**: `conversations.db` → `conversations`
**Description**: Every message sent/received during chatbot test sessions. Each session has 1-4 turns, each turn has a user message and a bot response.
**Primary Key**: `id` (INTEGER AUTOINCREMENT)
**Update Frequency**: Per test run (manual, ~weekly)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **id** | INTEGER | Auto-incrementing primary key | |
| **session_id** | TEXT | UUID identifying the conversation session | Groups all turns in one conversation |
| **category** | TEXT | Topic category of the test scenario | 10 categories: SBBU, Etablering, Flytning, etc. |
| **category_tag** | TEXT | Sub-classification tag | Only `SALES_HANDOVER_EXPECTED` for SBBU, NULL otherwise |
| **turn** | INTEGER | Turn number within the session | 1 = initial question, 2+ = follow-ups |
| **role** | TEXT | Who sent the message | `'user'` or `'bot'` |
| **text** | TEXT | The actual message content | Can be empty (scraper bug on some turn 2s) |
| **handover** | INTEGER | Whether handover was detected | 0 or 1. Only meaningful on `role='bot'` rows |
| **links** | TEXT | JSON array of URLs found in the message | `'[]'` if no links. Extracted during scraping |
| **dead_links** | TEXT | JSON array of verified broken URLs | `'[]'` if none. Populated by `check_links.js` |
| **timestamp** | DATETIME | When the row was inserted | SQLite CURRENT_TIMESTAMP format |

**Indexes**:
- `idx_session` on `session_id` — fast session lookups
- `idx_category` on `category` — fast category filtering

---

## Relationships

- **Session → Turns**: One session has 2-8 rows (1-4 turns × 2 roles)
- **Session → Scenario**: Maps to `scenarios.json` by category (not stored as FK)
- **Session → Follow-ups**: Maps to `followups.json` by session_id (not stored as FK)
- **Links → link_checks**: URLs in `links` column can be looked up in `link_checks` table

---

## Data Shape

Typical run produces:
- **49 scenarios** → 49 sessions minimum (single-turn)
- **~54 multi-turn sessions** (with 2-4 turns each)
- **Total**: ~100-200 sessions per run, ~400-800 rows

Per session:
- Turn 1: user question + bot answer (2 rows)
- Turn 2-4: follow-up question + bot answer (2 rows each)
- Total per session: 2-8 rows

---

## Sample Queries

### Count messages per session
```sql
SELECT session_id, category,
       COUNT(*) as messages,
       MAX(turn) as max_turn,
       SUM(CASE WHEN role='bot' AND handover=1 THEN 1 ELSE 0 END) as handovers
FROM conversations
GROUP BY session_id, category
ORDER BY category, session_id;
```

### Find bot responses mentioning specific topics
```sql
SELECT session_id, category, turn, text
FROM conversations
WHERE role = 'bot'
  AND text LIKE '%teknikerbesøg%'
ORDER BY category, turn;
```

### Sessions where bot gave empty response
```sql
SELECT c1.session_id, c1.category, c1.turn,
       c1.text as user_question
FROM conversations c1
LEFT JOIN conversations c2
  ON c1.session_id = c2.session_id
  AND c1.turn = c2.turn
  AND c2.role = 'bot'
WHERE c1.role = 'user'
  AND (c2.text IS NULL OR c2.text = '')
ORDER BY c1.category, c1.session_id, c1.turn;
```

---

## Common Gotchas

1. **Two rows per turn**: Each turn has both a user and bot row. When counting turns, use `MAX(turn)` not `COUNT(*)`.
2. **Handover only on bot rows**: The `handover` flag is only set on `role='bot'` rows. Filtering by `role='user' AND handover=1` will return nothing.
3. **Links are JSON strings**: To count links, use `JSON_ARRAY_LENGTH(links)` or `LENGTH(links) - LENGTH(REPLACE(links, 'http', ''))` as a rough count.
4. **Empty turn 2 bug**: In some test runs, all turn 2 bot responses are empty strings. This is a scraper/session-resumption bug, not a bot issue.
