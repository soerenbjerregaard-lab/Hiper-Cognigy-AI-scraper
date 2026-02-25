#!/usr/bin/env python3
# Phase 2 – Opfølgningsgenerering (manuel step)
#
# Kør dette script, copy-paste outputtet ind i Claude Code,
# og gem svaret som followups.json
#
# Usage: python3 phase2_generate.py

import sqlite3
import json
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'conversations.db')

def get_sessions(conn):
    return conn.execute("""
        SELECT
            session_id,
            category,
            category_tag,
            MAX(CASE WHEN role = 'user' AND turn = 1 THEN text END) AS question,
            MAX(CASE WHEN role = 'bot'  AND turn = 1 THEN text END) AS bot_answer
        FROM conversations
        GROUP BY session_id
        ORDER BY category, session_id
    """).fetchall()

def main():
    if not os.path.exists(DB_PATH):
        print(f"FEJL: Databasen '{DB_PATH}' ikke fundet. Kør phase1_scrape.js først.", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    sessions = get_sessions(conn)
    conn.close()

    if not sessions:
        print("FEJL: Ingen sessioner i databasen.", file=sys.stderr)
        sys.exit(1)

    print(f"# Phase 2: Opfølgningsgenerering – {len(sessions)} samtaler")
    print()
    print("Du er opfølgningsgenerator for en kundeservice-chatbot-test.")
    print("For hver samtale nedenfor skal du generere 2 naturlige opfølgningsspørgsmål.")
    print()
    print("Regler for opfølgningsspørgsmål:")
    print("1. Opfølgning 1: Kunden forstod ikke svaret / vil have det uddybet")
    print("2. Opfølgning 2: Et relateret problem der logisk følger af svaret")
    print("Skriv som en rigtig kunde ville – naturligt, dansk, evt. lidt utålmodigt.")
    print()
    print("Output HELE listen som én JSON-array – ingen tekst udenfor JSON-blokken:")
    print()
    print("```json")
    print("[")

    for i, (session_id, category, category_tag, question, bot_answer) in enumerate(sessions):
        bot_preview = (bot_answer or 'INGEN SVAR')[:300]
        if len(bot_answer or '') > 300:
            bot_preview += '...'

        comma = "," if i < len(sessions) - 1 else ""
        print(f"""  {{
    "session_id": "{session_id}",
    "category": "{category}",
    "original_question": {json.dumps(question or '', ensure_ascii=False)},
    "bot_answer_preview": {json.dumps(bot_preview, ensure_ascii=False)},
    "followup_1": "???",
    "followup_2": "???"
  }}{comma}""")

    print("]")
    print("```")
    print()
    print(f"# --- Instruktion ---")
    print(f"# Erstat alle \"???\" med rigtige opfølgningsspørgsmål.")
    print(f"# Gem outputtet som followups.json i projektmappen.")

if __name__ == '__main__':
    main()
