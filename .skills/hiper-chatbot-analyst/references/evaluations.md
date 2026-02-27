# Evaluations (Quality Scores)

Documentation for chatbot quality evaluation data — currently in rapport files, planned for DB migration.

---

## Quick Reference

### Business Context
Each test session is evaluated on multiple quality dimensions by Claude. The evaluations identify weaknesses in the chatbot's responses, track handover behavior, and flag hallucination risks. This data drives improvements to Cognigy's knowledge base and prompt configuration.

### Current State
Evaluation data lives in:
- `rapport-v2.md` — aggregated analysis with per-category scores
- CSV exports in `exports/` — raw conversation data (no scores yet)
- JSON output from `phase4_analyze.py` — structured evaluation per session

### Planned State
An `evaluations` table in SQLite to store per-session scores programmatically.

---

## Planned Table: evaluations

```sql
CREATE TABLE IF NOT EXISTS evaluations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT NOT NULL,
    category           TEXT NOT NULL,
    category_tag       TEXT,
    resolution_score   INTEGER CHECK(resolution_score BETWEEN 0 AND 5),
    context_retention  INTEGER CHECK(context_retention BETWEEN 0 AND 5),
    handover_triggered INTEGER NOT NULL DEFAULT 0,
    handover_justified INTEGER,  -- NULL if no handover triggered
    dead_links         TEXT NOT NULL DEFAULT '[]',  -- JSON array of dead URLs
    kb_gap             TEXT,     -- free text describing knowledge gap
    hallucination_risk INTEGER NOT NULL DEFAULT 0,
    notes              TEXT,     -- free text evaluation notes
    endpoint           TEXT,     -- 'gpt41', 'gpt5', etc.
    run_timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversations(session_id)
);
```

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| **session_id** | TEXT | Links to conversations table | FK |
| **category** | TEXT | Denormalized from conversations | For fast filtering |
| **resolution_score** | INTEGER | 0-5 quality score | 0=no help, 5=fully solved |
| **context_retention** | INTEGER | 0-5 context score | Only for multi-turn; NULL for single-turn |
| **handover_triggered** | INTEGER | Was handover detected? | 0/1 |
| **handover_justified** | INTEGER | Was handover appropriate? | 0/1/NULL (NULL if no handover) |
| **dead_links** | TEXT | JSON array of broken URLs | From link verification |
| **kb_gap** | TEXT | What knowledge was missing | Free text, NULL if none |
| **hallucination_risk** | INTEGER | Did bot invent facts? | 0/1 |
| **endpoint** | TEXT | Which AI endpoint was tested | 'gpt41', 'gpt5', etc. |
| **run_timestamp** | DATETIME | When this evaluation was created | Groups evaluations by test run |

---

## Scoring Rubric

### Resolution Score (0-5)
| Score | Meaning | Example |
|-------|---------|---------|
| 0 | No help at all | Bot crashed or completely off-topic |
| 1 | Off-topic or confusing | Bot answered a different question |
| 2 | Related but unhelpful | Bot understood topic but gave wrong/useless info |
| 3 | Partially solved | Some useful info but incomplete |
| 4 | Solved with workarounds | Correct answer but required extra steps or wasn't direct |
| 5 | Fully solved | Complete, accurate, actionable answer |

### Context Retention (0-5)
| Score | Meaning |
|-------|---------|
| 0 | Remembers nothing from previous turns |
| 1 | Vague awareness of topic only |
| 2 | Remembers topic but loses specifics |
| 3 | Adequate context, some repetition |
| 4 | Good context, minor gaps |
| 5 | Perfect — builds naturally on previous turns |

---

## Baseline Benchmarks (from rapport v2, 103 sessions)

### Resolution by Category
| Category | Single-turn | Multi-turn | Combined |
|----------|-------------|------------|----------|
| Flytning | 3.80 | 4.40 | 4.10 |
| Etablering | 3.60 | 4.40 | 4.00 |
| Hastighed | 3.20 | 4.00 | 3.60 |
| Regning | 3.67 | 3.50 | 3.58 |
| SBBU | 4.00 | 3.00 | 3.33 |
| Offline | 2.80 | 3.80 | 3.30 |
| Udstyr | 4.20 | 2.00 | 3.10 |
| Support øvrige | 3.40 | 2.60 | 3.00 |
| Ustabil | 2.00 | 2.20 | 2.10 |
| Øvrige | 3.25 | 1.00 | 2.00 |
| **TOTAL** | **3.39** | **3.09** | **3.23** |

### Key Findings
- Multi-turn degrades overall (3.39 → 3.09)
- SBBU and Udstyr degrade most in multi-turn (-1.0, -2.2)
- Ustabil and Øvrige are critically weak (<2.5 overall)
- 23% of sessions are GPT-5 candidates (need escalation)

---

## Sample Queries (for when evaluations table exists)

### Average scores per category
```sql
SELECT category,
       ROUND(AVG(resolution_score), 2) as avg_resolution,
       ROUND(AVG(context_retention), 2) as avg_context,
       COUNT(*) as sessions
FROM evaluations
GROUP BY category
ORDER BY avg_resolution DESC;
```

### Compare endpoints
```sql
SELECT endpoint, category,
       ROUND(AVG(resolution_score), 2) as avg_resolution,
       COUNT(*) as sessions
FROM evaluations
GROUP BY endpoint, category
ORDER BY endpoint, avg_resolution DESC;
```

### Sessions with knowledge gaps
```sql
SELECT e.session_id, e.category, e.kb_gap, e.resolution_score,
       e.notes
FROM evaluations e
WHERE e.kb_gap IS NOT NULL
ORDER BY e.resolution_score ASC;
```

### Hallucination risk sessions
```sql
SELECT e.session_id, e.category, e.resolution_score, e.notes
FROM evaluations e
WHERE e.hallucination_risk = 1
ORDER BY e.category;
```

### Handover accuracy
```sql
SELECT category,
       SUM(handover_triggered) as triggered,
       SUM(CASE WHEN handover_justified = 1 THEN 1 ELSE 0 END) as justified,
       SUM(CASE WHEN handover_triggered = 1 AND handover_justified = 0 THEN 1 ELSE 0 END) as false_positives,
       SUM(CASE WHEN handover_triggered = 0 AND category_tag = 'SALES_HANDOVER_EXPECTED' THEN 1 ELSE 0 END) as missed_handovers
FROM evaluations
GROUP BY category;
```
