# Links & Dead Link Tracking

Documentation for link extraction and verification in chatbot responses.

---

## Quick Reference

### Business Context
The chatbot frequently includes URLs in its responses (e.g. links to "Mit Hiper", help articles, or external resources). Dead links damage customer trust and indicate outdated knowledge base content. Link verification is a key quality signal.

---

## Table: link_checks

**Location**: `conversations.db` → `link_checks`
**Description**: Cache of HTTP status checks for URLs found in bot responses.
**Primary Key**: `url` (TEXT — the full URL)
**Update Frequency**: Per link check run (`node check_links.js`)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **url** | TEXT | The full URL that was checked | Primary key |
| **status_code** | INTEGER | HTTP status code returned | 200=OK, 404=Not Found, etc. |
| **ok** | INTEGER | Whether the link is alive | 0=dead, 1=alive |
| **checked_at** | DATETIME | When the check was performed | |

---

## Link Data Flow

1. **Extraction**: `run.js` extracts URLs from bot responses during scraping → stored in `conversations.links` as JSON array
2. **Verification**: `check_links.js` reads all unique URLs from conversations, performs HTTP HEAD/GET requests, stores results in `link_checks`
3. **Dead link tagging**: Results written back to `conversations.dead_links` column

---

## Sample Queries

### All dead links with context
```sql
SELECT c.session_id, c.category, c.turn, c.text,
       lc.url, lc.status_code
FROM conversations c
JOIN link_checks lc ON c.links LIKE '%' || lc.url || '%'
WHERE lc.ok = 0
ORDER BY c.category;
```

### Most common URLs in bot responses
```sql
SELECT lc.url, lc.ok, lc.status_code,
       COUNT(DISTINCT c.session_id) as sessions_containing
FROM link_checks lc
JOIN conversations c ON c.links LIKE '%' || lc.url || '%'
GROUP BY lc.url, lc.ok, lc.status_code
ORDER BY sessions_containing DESC;
```

### Dead link summary per category
```sql
SELECT category,
       COUNT(DISTINCT session_id) as sessions_with_dead_links,
       dead_links
FROM conversations
WHERE dead_links != '[]' AND dead_links != ''
GROUP BY category
ORDER BY sessions_with_dead_links DESC;
```

### All verified links and their status
```sql
SELECT url, status_code, ok,
       checked_at
FROM link_checks
ORDER BY ok ASC, status_code DESC;
```

---

## Common Gotchas

1. **LIKE for JSON matching**: Since links are stored as JSON text, use `LIKE '%url%'` for joining. This is imprecise but works for the small dataset.
2. **dead_links vs link_checks**: `dead_links` on conversations is a denormalized copy. The source of truth for link status is `link_checks`.
3. **Some links may not be checked**: If `check_links.js` hasn't been run after a scraping session, `link_checks` may be stale.

## Known Dead Links (from v2 rapport)

5 unique dead links were identified affecting 6 sessions. Two are critical (offline help page and cancellation page).
