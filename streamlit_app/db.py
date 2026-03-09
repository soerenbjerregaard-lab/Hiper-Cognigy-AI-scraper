import sqlite3
import os
from pathlib import Path

DB_PATH = os.environ.get(
    "SIMLAB_DB",
    str(Path(__file__).parent.parent / "simlab.db"),
)

# ── Business hours config ─────────────────────────────────────────────────────
# Handover udenfor disse timer er teknisk, men kunden kan ikke nå en reel agent.
BUSINESS_HOURS_START = 8   # 08:00 (inklusiv)
BUSINESS_HOURS_END   = 16  # 16:00 (eksklusiv)


def _in_biz_hours(ts_col="r.run_started_at"):
    """SQL fragment: TRUE hvis kørslen startede i åbningstiden."""
    h = f"CAST(strftime('%H', {ts_col}) AS INTEGER)"
    return f"({h} >= {BUSINESS_HOURS_START} AND {h} < {BUSINESS_HOURS_END})"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, params=()):
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def execute(sql, params=()):
    conn = get_conn()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


# ── Home ──────────────────────────────────────────────────────────────────────

def get_kpis():
    return query("""
        SELECT
            COUNT(DISTINCT run_id)                                                         AS runs,
            COUNT(DISTINCT session_id)                                                     AS sessions,
            ROUND(AVG(handover_flag) * 100, 1)                                             AS handover_rate_pct,
            ROUND(AVG(CASE WHEN error_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)            AS session_error_rate_pct,
            ROUND(AVG(CASE WHEN dead_link_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)        AS dead_link_session_rate_pct,
            ROUND(AVG(CASE WHEN turns_total >= 4 THEN 1.0 ELSE 0 END) * 100, 1)           AS reach_t4_pct
        FROM sessions
    """)


def get_runs_over_time():
    return query("""
        SELECT DATE(run_started_at) AS run_date, COUNT(*) AS runs, SUM(session_count) AS sessions
        FROM runs GROUP BY 1 ORDER BY 1
    """)


def get_endpoint_summary():
    return query("""
        SELECT
            endpoint,
            COUNT(*) AS sessions,
            ROUND(AVG(handover_flag) * 100, 1)                                          AS handover_rate_pct,
            ROUND(AVG(CASE WHEN error_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)         AS error_rate_pct,
            ROUND(AVG(CASE WHEN dead_link_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)     AS dead_link_rate_pct,
            ROUND(AVG(turns_total), 2)                                                  AS avg_turns
        FROM sessions GROUP BY 1 ORDER BY sessions DESC
    """)


def get_run_health():
    in_h = _in_biz_hours()
    return query(f"""
        SELECT
            r.run_started_at,
            SUBSTR(r.run_id, 1, 8)                                                      AS run_short,
            r.endpoint,
            r.session_count,
            ROUND(AVG(CASE WHEN s.error_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)      AS error_rate_pct,
            ROUND(AVG(CASE WHEN s.timeout_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)    AS timeout_rate_pct,
            ROUND(AVG(CASE WHEN s.dead_link_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)  AS dead_link_rate_pct,
            ROUND(AVG(s.handover_flag) * 100, 1)                                        AS handover_rate_pct,
            CASE WHEN {in_h} THEN '✅' ELSE '⛔' END                                    AS i_aabningstid
        FROM runs r JOIN sessions s ON s.run_id = r.run_id
        GROUP BY 1,2,3,4 ORDER BY r.run_started_at DESC
    """)


def get_handover_by_hours():
    """Handover-rate opdelt på åbningstid vs. udenfor.
    Returnerer maks 2 rækker: period='in_hours' | 'out_of_hours'."""
    in_h = _in_biz_hours()
    return query(f"""
        SELECT
            CASE WHEN {in_h} THEN 'in_hours' ELSE 'out_of_hours' END AS period,
            COUNT(DISTINCT s.session_id)                               AS sessions,
            ROUND(AVG(s.handover_flag) * 100, 1)                      AS handover_rate_pct
        FROM sessions s
        JOIN runs r ON r.run_id = s.run_id
        GROUP BY 1
    """)


def get_category_summary():
    """Per-category performance: handover, errors, dead links, avg turns."""
    return query("""
        SELECT
            category,
            COUNT(*)                                                                        AS sessions,
            ROUND(AVG(handover_flag) * 100, 1)                                             AS handover_pct,
            ROUND(AVG(CASE WHEN error_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)            AS error_pct,
            ROUND(AVG(CASE WHEN dead_link_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)        AS deadlink_pct,
            ROUND(AVG(turns_total), 1)                                                     AS avg_turns
        FROM sessions
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY handover_pct DESC
    """)


def get_handover_turn_distribution():
    """For sessions WITH handover: how many at turn 1, 2, 3+.
    Returns at most 3 rows – all turns >= 3 are collapsed into one."""
    return query("""
        SELECT
            CASE
                WHEN handover_turn = 1 THEN 1
                WHEN handover_turn = 2 THEN 2
                ELSE 3
            END AS handover_turn,
            COUNT(*) AS sessions
        FROM sessions
        WHERE handover_flag = 1
          AND handover_turn IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """)


def get_judge_aggregate():
    """Overall AI judge averages across all judged sessions."""
    rows = query("""
        SELECT
            COUNT(DISTINCT session_id)                  AS judged_sessions,
            ROUND(AVG(response_quality), 2)             AS avg_quality,
            ROUND(AVG(context_coherence), 2)            AS avg_context,
            ROUND(AVG(helpfulness), 2)                  AS avg_helpfulness,
            ROUND(AVG(confidence), 2)                   AS avg_confidence,
            ROUND(100.0 * SUM(CASE WHEN handover_assessment = 'unnecessary' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0), 1)             AS unnecessary_handover_pct,
            ROUND(100.0 * SUM(CASE WHEN handover_assessment = 'missing' THEN 1 ELSE 0 END)
                  / NULLIF(COUNT(*), 0), 1)             AS missing_handover_pct
        FROM ai_judgements
    """)
    return rows[0] if rows else None


def get_quality_trend_by_run():
    """Average AI judge scores per run, ordered by run date."""
    return query("""
        SELECT
            r.run_started_at,
            r.endpoint,
            COUNT(DISTINCT j.session_id)        AS judged,
            ROUND(AVG(j.response_quality), 2)   AS avg_quality,
            ROUND(AVG(j.helpfulness), 2)        AS avg_helpfulness,
            ROUND(AVG(j.context_coherence), 2)  AS avg_context
        FROM ai_judgements j
        JOIN sessions s ON s.session_id = j.session_id
        JOIN runs r ON r.run_id = s.run_id
        GROUP BY r.run_id, r.run_started_at, r.endpoint
        ORDER BY r.run_started_at
    """)


def get_top_handover_questions(limit=5):
    """Return questions with highest handover rate, min 2 sessions."""
    return query("""
        SELECT MIN(first_user_text) AS question_text,
               MIN(category)        AS category,
               COUNT(*)             AS sessions,
               ROUND(AVG(handover_flag) * 100, 1) AS handover_rate_pct
        FROM sessions
        GROUP BY question_key
        HAVING COUNT(*) >= 2
        ORDER BY handover_rate_pct DESC
        LIMIT ?
    """, (limit,))


# ── Scenario Compare ──────────────────────────────────────────────────────────

def get_topic_options():
    return query("""
        SELECT question_key, MIN(category) || '  ·  ' || MIN(first_user_text) AS label
        FROM sessions GROUP BY 1 ORDER BY MIN(category), MIN(first_user_text)
    """)


def get_session_options(question_key):
    return query("""
        SELECT s.session_id,
               r.run_started_at || '  ·  ' || s.endpoint || '  ·  ' || COALESCE(s.scenario_label, s.category) AS label
        FROM sessions s JOIN runs r ON r.run_id = s.run_id
        WHERE s.question_key = ?
        ORDER BY r.run_started_at DESC
    """, (question_key,))


def get_default_sessions(question_key):
    return query("""
        SELECT session_id, ROW_NUMBER() OVER (ORDER BY run_started_at DESC) AS slot
        FROM (
            SELECT MIN(s.session_id) AS session_id, r.run_started_at
            FROM sessions s JOIN runs r ON r.run_id = s.run_id
            WHERE s.question_key = ?
            GROUP BY s.run_id, r.run_started_at
            ORDER BY r.run_started_at DESC
        )
    """, (question_key,))


def get_session_meta(session_id):
    return query("""
        SELECT r.run_started_at, s.endpoint, s.turns_total, s.handover_flag,
               s.handover_turn, s.error_count, s.dead_link_count,
               ROUND(s.avg_bot_chars) AS avg_bot_chars
        FROM sessions s JOIN runs r ON r.run_id = s.run_id
        WHERE s.session_id = ?
    """, (session_id,))


def get_conversation(session_id):
    return query("""
        SELECT turn, role, handover,
               REPLACE(REPLACE(REPLACE(REPLACE(text,'<p>',''),'</p>',''),'<br/>','<br>'),'<br />','<br>') AS text,
               dead_links_json, timestamp
        FROM turns WHERE session_id = ?
        ORDER BY turn, CASE WHEN role='user' THEN 0 ELSE 1 END
    """, (session_id,))


def get_latest_judge(session_id):
    rows = query("""
        SELECT judged_at, response_quality, context_coherence, helpfulness,
               handover_assessment, handover_should_have_happened, handover_unnecessary,
               confidence, summary, analysis_notes
        FROM ai_judgements WHERE session_id = ?
        ORDER BY judged_at DESC LIMIT 1
    """, (session_id,))
    return rows[0] if rows else None


def get_judge_history(session_id):
    return query("""
        SELECT judged_at, prompt_version, judge_model, response_quality,
               context_coherence, helpfulness, handover_assessment, confidence, summary
        FROM ai_judgements WHERE session_id = ?
        ORDER BY judged_at DESC
    """, (session_id,))


def get_turns_for_judge(session_id):
    return query("""
        SELECT turn, role, text FROM turns WHERE session_id = ?
        ORDER BY turn, CASE WHEN role='user' THEN 0 ELSE 1 END
    """, (session_id,))


def get_session_run_id(session_id):
    rows = query("SELECT run_id FROM sessions WHERE session_id = ?", (session_id,))
    return rows[0]["run_id"] if rows else None


def save_judgement(session_id, run_id, prompt_version, judge_model, judge):
    execute("""
        INSERT INTO ai_judgements (
            session_id, run_id, prompt_version, judge_model,
            response_quality, context_coherence, helpfulness,
            handover_assessment, handover_should_have_happened, handover_unnecessary,
            dead_links_found, summary, analysis_notes, confidence, inconclusive_reason, raw_json
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        session_id, run_id, prompt_version, judge_model,
        judge["response_quality"], judge["context_coherence"], judge["helpfulness"],
        judge["handover_assessment"], judge["handover_should_have_happened"], judge["handover_unnecessary"],
        judge["dead_links_found"], judge["summary"], judge["analysis_notes"],
        judge["confidence"], judge["inconclusive_reason"],
        str(judge),
    ))


# ── Conversation Explorer ─────────────────────────────────────────────────────

def get_run_options():
    return query("""
        SELECT run_id, run_started_at || '  ·  ' || endpoint AS label
        FROM runs ORDER BY run_started_at DESC
    """)


def get_sessions_for_run(run_id=None):
    if run_id:
        return query("""
            SELECT s.session_id,
                   r.run_started_at || '  ·  ' || s.category || '  ·  ' || s.first_user_text AS label
            FROM sessions s JOIN runs r ON r.run_id = s.run_id
            WHERE s.run_id = ? ORDER BY r.run_started_at DESC
        """, (run_id,))
    return query("""
        SELECT s.session_id,
               r.run_started_at || '  ·  ' || s.category || '  ·  ' || s.first_user_text AS label
        FROM sessions s JOIN runs r ON r.run_id = s.run_id
        ORDER BY r.run_started_at DESC
    """)


# ── Question Deep Dive ────────────────────────────────────────────────────────

def get_question_options():
    return query("""
        SELECT question_key, MIN(category) || '  ·  ' || MIN(first_user_text) AS label
        FROM sessions GROUP BY 1 ORDER BY MIN(category), MIN(first_user_text)
    """)


def get_question_overview(question_key):
    return query("""
        SELECT MIN(first_user_text) AS question_text, MIN(category) AS category,
               COUNT(*) AS sessions,
               ROUND(AVG(handover_flag) * 100, 1)                                       AS handover_rate_pct,
               ROUND(AVG(CASE WHEN error_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)      AS error_rate_pct,
               ROUND(AVG(CASE WHEN dead_link_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)  AS dead_link_rate_pct,
               ROUND(AVG(turns_total), 2)                                               AS avg_turns
        FROM sessions WHERE question_key = ?
    """, (question_key,))


def get_question_by_run(question_key):
    return query("""
        SELECT r.run_started_at, s.endpoint, COUNT(*) AS sessions,
               ROUND(AVG(s.handover_flag) * 100, 1)                                        AS handover_rate_pct,
               ROUND(AVG(CASE WHEN s.error_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)       AS error_rate_pct,
               ROUND(AVG(CASE WHEN s.dead_link_count > 0 THEN 1.0 ELSE 0 END) * 100, 1)   AS dead_link_rate_pct,
               ROUND(AVG(s.turns_total), 2)                                                 AS avg_turns
        FROM sessions s JOIN runs r ON r.run_id = s.run_id
        WHERE s.question_key = ?
        GROUP BY 1,2 ORDER BY r.run_started_at
    """, (question_key,))


# ── Dead Links ────────────────────────────────────────────────────────────────

def get_dead_link_urls():
    """Alle døde link-URL'er på tværs af alle kørsler, sorteret efter hyppighed."""
    return query("""
        SELECT
            j.value                         AS url,
            COUNT(*)                        AS hits,
            COUNT(DISTINCT t.session_id)    AS sessions
        FROM turns t, json_each(t.dead_links_json) j
        WHERE t.dead_links_json IS NOT NULL
          AND t.dead_links_json NOT IN ('[]', '')
        GROUP BY 1
        ORDER BY 2 DESC
    """)


def get_dead_links_by_category():
    """Antal sessioner med døde links og unikke URLs per emneområde."""
    return query("""
        SELECT
            s.category,
            COUNT(DISTINCT s.session_id)    AS sessions_with_deadlinks,
            COUNT(DISTINCT j.value)         AS unique_urls,
            COUNT(*)                        AS total_hits
        FROM sessions s
        JOIN turns t ON t.session_id = s.session_id,
             json_each(t.dead_links_json) j
        WHERE t.dead_links_json IS NOT NULL
          AND t.dead_links_json NOT IN ('[]', '')
          AND s.category IS NOT NULL
        GROUP BY 1
        ORDER BY 2 DESC
    """)


def get_dead_links_by_run():
    """Antal sessioner med døde links og total hits per kørsel."""
    return query("""
        SELECT
            r.run_started_at,
            r.endpoint,
            COUNT(DISTINCT s.session_id)    AS sessions_with_deadlinks,
            COUNT(DISTINCT j.value)         AS unique_urls,
            COUNT(*)                        AS total_hits
        FROM sessions s
        JOIN runs r ON r.run_id = s.run_id
        JOIN turns t ON t.session_id = s.session_id,
             json_each(t.dead_links_json) j
        WHERE t.dead_links_json IS NOT NULL
          AND t.dead_links_json NOT IN ('[]', '')
        GROUP BY r.run_id, r.run_started_at, r.endpoint
        ORDER BY r.run_started_at DESC
    """)
