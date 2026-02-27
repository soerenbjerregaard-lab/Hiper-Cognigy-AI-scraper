# Key Metrics & KPI Calculations

All metrics used in Hiper chatbot quality analysis.

---

## Primary Metrics

### 1. Resolution Score (per session)
- **Definition**: How completely the bot resolved the customer's issue
- **Scale**: 0-5 (integer)
- **Source**: `evaluations.resolution_score` (planned) or rapport files
- **Aggregation**: AVG per category, per endpoint, or overall
- **Target**: ≥ 4.0 per category

```sql
-- Average resolution per category
SELECT category,
       ROUND(AVG(resolution_score), 2) as avg_resolution,
       MIN(resolution_score) as worst,
       MAX(resolution_score) as best,
       COUNT(*) as n
FROM evaluations
GROUP BY category
ORDER BY avg_resolution;
```

### 2. Context Retention (per multi-turn session)
- **Definition**: How well the bot maintains conversation context across turns
- **Scale**: 0-5 (integer)
- **Applies to**: Multi-turn sessions only (max_turn > 1)
- **Target**: ≥ 4.0

```sql
-- Context retention per category (multi-turn only)
SELECT e.category,
       ROUND(AVG(e.context_retention), 2) as avg_context,
       COUNT(*) as n
FROM evaluations e
WHERE e.context_retention IS NOT NULL
GROUP BY e.category
ORDER BY avg_context;
```

### 3. Multi-turn Degradation
- **Definition**: Drop in resolution score from single-turn to multi-turn sessions
- **Formula**: `AVG(resolution_score WHERE max_turn=1) - AVG(resolution_score WHERE max_turn>1)`
- **Positive value = degradation** (multi-turn is worse)
- **Target**: ≤ 0.3 (minimal degradation)

```sql
-- Multi-turn degradation per category
WITH session_types AS (
    SELECT session_id, category, MAX(turn) as max_turn
    FROM conversations
    GROUP BY session_id, category
)
SELECT st.category,
       ROUND(AVG(CASE WHEN st.max_turn = 1 THEN e.resolution_score END), 2) as single_avg,
       ROUND(AVG(CASE WHEN st.max_turn > 1 THEN e.resolution_score END), 2) as multi_avg,
       ROUND(AVG(CASE WHEN st.max_turn = 1 THEN e.resolution_score END) -
             AVG(CASE WHEN st.max_turn > 1 THEN e.resolution_score END), 2) as degradation
FROM evaluations e
JOIN session_types st ON e.session_id = st.session_id
GROUP BY st.category
ORDER BY degradation DESC;
```

### 4. Handover Rate
- **Definition**: Percentage of sessions where the bot escalated to human
- **Source**: `conversations.handover` column (bot rows only)

```sql
-- From conversations table directly
SELECT category,
       COUNT(DISTINCT session_id) as total_sessions,
       COUNT(DISTINCT CASE WHEN handover = 1 THEN session_id END) as handover_sessions,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN handover = 1 THEN session_id END) /
             COUNT(DISTINCT session_id), 1) as handover_pct
FROM conversations
WHERE role = 'bot'
GROUP BY category;
```

### 5. Handover Precision
- **Definition**: Of all triggered handovers, how many were justified?
- **Formula**: `justified_handovers / triggered_handovers`
- **Source**: `evaluations` table
- **Note**: For SBBU (category_tag='SALES_HANDOVER_EXPECTED'), handover is always justified

### 6. Dead Link Rate
- **Definition**: Sessions containing at least one broken URL
- **Source**: `conversations.dead_links` column + `link_checks` table

```sql
-- Dead link rate per category
SELECT category,
       COUNT(DISTINCT session_id) as total_sessions,
       COUNT(DISTINCT CASE WHEN dead_links != '[]' AND dead_links != ''
             THEN session_id END) as sessions_with_dead_links,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN dead_links != '[]' AND dead_links != ''
             THEN session_id END) / COUNT(DISTINCT session_id), 1) as dead_link_pct
FROM conversations
WHERE role = 'bot'
GROUP BY category;
```

### 7. Knowledge Gap Frequency
- **Definition**: Most common topics where the bot lacks knowledge
- **Source**: `evaluations.kb_gap` (free text)
- **Analysis**: Group by keyword/theme manually or with text analysis

---

## Composite / Derived Metrics

### Overall Quality Index
- **Formula**: `(AVG(resolution_score) * 0.5) + (AVG(context_retention) * 0.3) + ((1 - dead_link_rate) * 0.2) * 5`
- **Scale**: 0-5
- **Weights**: Resolution most important (50%), then context (30%), then link quality (20%)

### GPT-5 Candidate Rate
- **Definition**: Sessions that scored poorly enough to warrant testing with GPT-5
- **Threshold**: `resolution_score <= 2 OR (resolution_score = 3 AND hallucination_risk = 1)`
- **Benchmark**: 23% in v2 rapport

---

## Benchmark Tracking

When comparing across runs/endpoints, key comparisons are:

1. **Same scenarios, different endpoints**: GPT-4.1 vs GPT-5 on identical questions
2. **Same endpoint, over time**: Track improvement as Cognigy config is updated
3. **Category trends**: Which categories improve/regress between runs
