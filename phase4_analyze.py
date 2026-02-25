#!/usr/bin/env python3
# Phase 4 – Kvalitetsanalyse
#
# Læser alle samtaler fra DB og printer en analyse-prompt til Claude Code.
# Copy-paste outputtet ind i Claude Code og gem resultatet som rapport.md
#
# Usage: python3 phase4_analyze.py [--session SESSION_ID]
#        python3 phase4_analyze.py  → analyserer alle sessioner

import sqlite3
import json
import sys
import os
import argparse

DB_PATH = os.path.join(os.path.dirname(__file__), 'conversations.db')

EVAL_SCHEMA = """{
  "session_id": "...",
  "category": "...",
  "category_tag": "..." | null,
  "resolution_score": 0-5,
  "context_retention": 0-5,
  "handover_triggered": true | false,
  "handover_justified": true | false | null,
  "dead_links": ["url1", "url2"],
  "kb_gap": "Hvad manglede botten viden om – eller null",
  "hallucination_risk": true | false,
  "notes": "Kort fri tekst"
}"""

def get_threads(conn, session_filter=None):
    query = """
        SELECT session_id, category, category_tag, turn, role, text, handover, links
        FROM conversations
        {}
        ORDER BY session_id, turn, CASE role WHEN 'user' THEN 0 ELSE 1 END
    """.format("WHERE session_id = ?" if session_filter else "")

    rows = conn.execute(query, (session_filter,) if session_filter else ()).fetchall()

    # Gruppér per session
    sessions = {}
    for session_id, category, category_tag, turn, role, text, handover, links in rows:
        if session_id not in sessions:
            sessions[session_id] = {
                'session_id': session_id,
                'category': category,
                'category_tag': category_tag,
                'turns': []
            }
        sessions[session_id]['turns'].append({
            'turn': turn, 'role': role, 'text': text,
            'handover': bool(handover),
            'links': json.loads(links or '[]')
        })

    return list(sessions.values())

def format_thread(session):
    lines = []
    for t in session['turns']:
        prefix = 'KUNDE' if t['role'] == 'user' else 'BOT'
        handover_note = ' ← HANDOVER DETEKTERET' if t['handover'] and t['role'] == 'bot' else ''
        lines.append(f"  Turn {t['turn']} [{prefix}]: {t['text']}{handover_note}")
        if t['links']:
            lines.append(f"           Links: {', '.join(t['links'])}")
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', help='Analyser kun én session (session_id)')
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"FEJL: Databasen '{DB_PATH}' ikke fundet.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    sessions = get_threads(conn, args.session)
    conn.close()

    if not sessions:
        print("FEJL: Ingen samtaler i databasen.", file=sys.stderr)
        sys.exit(1)

    print(f"# Phase 4: Kvalitetsanalyse – {len(sessions)} samtaler")
    print()
    print("Du er quality assessor for Hipers AI-chatbot (Cognigy).")
    print("Evaluer HVER samtale nedenfor og returner præcis ét JSON-objekt per samtale.")
    print()
    print("Scoringsskala:")
    print("  resolution_score  0=ingen hjælp, 5=fuldstændig løsning")
    print("  context_retention 0=huker intet, 5=perfekt kontekst på tværs af turns")
    print()
    print("Særregel for SALES_HANDOVER_EXPECTED: handover_justified=true er normalt/forventet.")
    print("hallucination_risk=true hvis botten opfandt faktuelle detaljer der ikke kan verificeres.")
    print()
    print("Output HELE listen som én JSON-array – ingen tekst udenfor JSON:")
    print()
    print("```json")
    print("[")

    for i, session in enumerate(sessions):
        comma = "," if i < len(sessions) - 1 else ""
        thread_str = format_thread(session)
        print(f"""  {{
    "session_id": "{session['session_id']}",
    "category": "{session['category']}",
    "category_tag": {json.dumps(session['category_tag'])},
    "samtale": [
{chr(10).join('      ' + json.dumps(t, ensure_ascii=False) for t in session['turns'])}
    ],
    "resolution_score": null,
    "context_retention": null,
    "handover_triggered": null,
    "handover_justified": null,
    "dead_links": [],
    "kb_gap": null,
    "hallucination_risk": null,
    "notes": null
  }}{comma}""")

    print("]")
    print("```")
    print()
    print("# Aggregeret rapport (tilføj efter JSON-arrayet):")
    print("# - Gennemsnitlig resolution_score per kategori")
    print("# - Top 10 hyppigste kb_gap-emner")
    print("# - Liste over alle dead_links")
    print("# - Handover: triggered count vs. justified count")
    print("# - Sessioner med hallucination_risk=true")

if __name__ == '__main__':
    main()
