#!/usr/bin/env python3
import csv
import glob
import hashlib
import json
import os
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXPORTS_DIR = ROOT / 'exports'
SCENARIOS_FILE = ROOT / 'scenarios.json'
SCENARIOS_EXT_FILE = ROOT / 'scenarios-extended.json'
DB_PATH = ROOT / 'evidence-dashboard' / 'sources' / 'simlab' / 'simlab.db'
JUDGE_PROMPT_FILE = ROOT / 'evidence-dashboard' / 'judge_prompt_v1.txt'


def normalize_text(s: str) -> str:
    return ' '.join((s or '').strip().split()).lower()


def stable_question_key(category: str, q1: str) -> str:
    base = f"{category}|{normalize_text(q1)}"
    return hashlib.sha1(base.encode('utf-8')).hexdigest()[:16]


def parse_run_started_at(file_name: str):
    # conversations-<endpoint>-HH.MM-DD-MM-YYYY.csv
    # Some historical files differ; fallback to file mtime.
    stem = Path(file_name).stem
    parts = stem.split('-')
    if len(parts) >= 4:
        try:
            ts = f"{parts[-3]}-{parts[-2]}-{parts[-1]}"
            return datetime.strptime(ts, '%H.%M-%d-%m-%Y')
        except Exception:
            return None
    return None


def load_scenario_maps():
    lookup = {}
    scenarios = []

    if SCENARIOS_FILE.exists():
        with open(SCENARIOS_FILE, encoding='utf-8') as fh:
            base = json.load(fh)
        for s in base:
            sid = int(s.get('id'))
            cat = s.get('category', '')
            q1 = (s.get('questions') or [''])[0]
            key = stable_question_key(cat, q1)
            lookup[(cat, normalize_text(q1))] = {
                'scenario_id': sid,
                'scenario_label': f"S{sid:02d}",
                'question_key': key,
                'variation_id': None,
                'persona': None,
                'topic': None,
                'intent': None,
            }
            scenarios.append((sid, f"S{sid:02d}", cat, key, q1, None, None, None, None))

    if SCENARIOS_EXT_FILE.exists():
        with open(SCENARIOS_EXT_FILE, encoding='utf-8') as fh:
            ext = json.load(fh)
        for s in ext:
            sid = int(s.get('id'))
            cat = s.get('category', '')
            topic = s.get('topic')
            intent = s.get('intent')
            variations = s.get('variations') or []
            for v in variations:
                v_id = v.get('id')
                persona = v.get('persona')
                q1 = v.get('q1') or ''
                key = stable_question_key(cat, q1)
                lookup[(cat, normalize_text(q1))] = {
                    'scenario_id': sid,
                    'scenario_label': f"S{sid:02d}",
                    'question_key': key,
                    'variation_id': v_id,
                    'persona': persona,
                    'topic': topic,
                    'intent': intent,
                }
                scenarios.append((sid, f"S{sid:02d}", cat, key, q1, v_id, persona, topic, intent))

    dedup = {}
    for row in scenarios:
        dedup[(row[2], row[3], row[5] or '')] = row
    return lookup, list(dedup.values())


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    prompt_text = JUDGE_PROMPT_FILE.read_text(encoding='utf-8') if JUDGE_PROMPT_FILE.exists() else ''

    cur.executescript(
        '''
        PRAGMA journal_mode = WAL;

        CREATE TABLE runs (
            run_id TEXT PRIMARY KEY,
            endpoint TEXT,
            export_file TEXT,
            run_started_at TEXT,
            row_count INTEGER,
            session_count INTEGER
        );

        CREATE TABLE scenarios (
            scenario_id INTEGER,
            scenario_label TEXT,
            category TEXT,
            question_key TEXT,
            question_text TEXT,
            variation_id TEXT,
            persona TEXT,
            topic TEXT,
            intent TEXT,
            PRIMARY KEY (scenario_id, question_key, variation_id)
        );

        CREATE TABLE sessions (
            session_id TEXT,
            run_id TEXT,
            endpoint TEXT,
            category TEXT,
            category_tag TEXT,
            scenario_id INTEGER,
            scenario_label TEXT,
            question_key TEXT,
            variation_id TEXT,
            persona TEXT,
            topic TEXT,
            intent TEXT,
            first_user_text TEXT,
            turns_total INTEGER,
            bot_turns INTEGER,
            user_turns INTEGER,
            error_count INTEGER,
            timeout_count INTEGER,
            handover_turn INTEGER,
            handover_flag INTEGER,
            dead_link_turns INTEGER,
            dead_link_count INTEGER,
            avg_bot_chars REAL,
            created_at_min TEXT,
            created_at_max TEXT,
            PRIMARY KEY (session_id)
        );

        CREATE TABLE turns (
            row_id INTEGER,
            run_id TEXT,
            endpoint TEXT,
            session_id TEXT,
            category TEXT,
            category_tag TEXT,
            scenario_id INTEGER,
            question_key TEXT,
            turn INTEGER,
            role TEXT,
            text TEXT,
            handover INTEGER,
            links_json TEXT,
            dead_links_json TEXT,
            timestamp TEXT
        );

        CREATE TABLE ai_judgements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            run_id TEXT,
            prompt_version TEXT,
            judge_model TEXT NOT NULL,
            response_quality REAL,
            context_coherence REAL,
            helpfulness REAL,
            handover_assessment TEXT,
            handover_should_have_happened INTEGER,
            handover_unnecessary INTEGER,
            dead_links_found INTEGER,
            summary TEXT,
            analysis_notes TEXT,
            confidence REAL,
            inconclusive_reason TEXT,
            raw_json TEXT,
            judged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE judge_config (
            config_key TEXT PRIMARY KEY,
            config_value TEXT
        );

        CREATE INDEX idx_sessions_run ON sessions(run_id);
        CREATE INDEX idx_sessions_scenario ON sessions(scenario_id, question_key);
        CREATE INDEX idx_turns_session ON turns(session_id, turn, role);
        CREATE INDEX idx_turns_run ON turns(run_id);
        CREATE INDEX idx_judgements_session ON ai_judgements(session_id, judged_at);
        '''
    )

    cur.execute('INSERT INTO judge_config (config_key, config_value) VALUES (?, ?)', ('prompt_version', 'v1'))
    cur.execute('INSERT INTO judge_config (config_key, config_value) VALUES (?, ?)', ('judge_prompt', prompt_text))
    cur.execute('INSERT INTO judge_config (config_key, config_value) VALUES (?, ?)', ('default_model', 'qwen2.5:3b-instruct'))

    scenario_lookup, scenario_rows = load_scenario_maps()
    cur.executemany(
        '''
        INSERT INTO scenarios (
            scenario_id, scenario_label, category, question_key, question_text,
            variation_id, persona, topic, intent
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        scenario_rows,
    )

    files = sorted(glob.glob(str(EXPORTS_DIR / '*.csv')))
    for file_path in files:
        rows = []
        with open(file_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append(row)

        if not rows:
            continue

        run_id = rows[0].get('run_id') or Path(file_path).stem
        endpoint_candidates = [r.get('endpoint') for r in rows if r.get('endpoint')]
        endpoint = endpoint_candidates[0] if endpoint_candidates else 'unknown'
        run_started = parse_run_started_at(file_path)
        if run_started is None:
            run_started = datetime.fromtimestamp(os.path.getmtime(file_path))

        sessions = defaultdict(list)
        for r in rows:
            sessions[r['session_id']].append(r)

        cur.execute(
            '''
            INSERT INTO runs (run_id, endpoint, export_file, run_started_at, row_count, session_count)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
              endpoint=excluded.endpoint,
              export_file=excluded.export_file,
              run_started_at=excluded.run_started_at,
              row_count=excluded.row_count,
              session_count=excluded.session_count
            ''',
            (
                run_id,
                endpoint,
                os.path.basename(file_path),
                run_started.isoformat(timespec='seconds'),
                len(rows),
                len(sessions),
            ),
        )

        for session_id, srows in sessions.items():
            srows_sorted = sorted(srows, key=lambda x: (int(x.get('turn') or 0), x.get('role') or ''))
            category = srows_sorted[0].get('category')
            category_tag = srows_sorted[0].get('category_tag')

            user_turn1 = ''
            for r in srows_sorted:
                if r.get('role') == 'user' and str(r.get('turn')) == '1':
                    user_turn1 = r.get('text', '')
                    break

            scenario_meta = scenario_lookup.get((category, normalize_text(user_turn1)))
            if scenario_meta:
                scenario_id = scenario_meta['scenario_id']
                scenario_label = scenario_meta['scenario_label']
                question_key = scenario_meta['question_key']
                variation_id = scenario_meta['variation_id']
                persona = scenario_meta['persona']
                topic = scenario_meta['topic']
                intent = scenario_meta['intent']
            else:
                scenario_id = None
                scenario_label = None
                question_key = stable_question_key(category or 'unknown', user_turn1 or session_id)
                variation_id = None
                persona = None
                topic = None
                intent = None

            bot_rows = [r for r in srows_sorted if r.get('role') == 'bot']
            user_rows = [r for r in srows_sorted if r.get('role') == 'user']

            handover_turn = None
            for r in bot_rows:
                if str(r.get('handover')) == '1':
                    handover_turn = int(r.get('turn') or 0)
                    break

            def safe_json_count(v):
                try:
                    arr = json.loads(v or '[]')
                    return len(arr) if isinstance(arr, list) else 0
                except Exception:
                    return 0

            dead_link_turns = 0
            dead_link_count = 0
            for r in bot_rows:
                cnt = safe_json_count(r.get('dead_links', '[]'))
                dead_link_count += cnt
                if cnt > 0:
                    dead_link_turns += 1

            error_count = sum(1 for r in bot_rows if (r.get('text') or '').startswith('ERROR:'))
            timeout_count = sum(1 for r in bot_rows if (r.get('text') or '').startswith('ERROR: timeout'))
            avg_bot_chars = (sum(len(r.get('text') or '') for r in bot_rows) / len(bot_rows)) if bot_rows else 0

            timestamps = [r.get('timestamp') for r in srows_sorted if r.get('timestamp')]
            created_at_min = min(timestamps) if timestamps else None
            created_at_max = max(timestamps) if timestamps else None

            cur.execute(
                '''
                INSERT OR REPLACE INTO sessions (
                    session_id, run_id, endpoint, category, category_tag,
                    scenario_id, scenario_label, question_key, variation_id, persona, topic, intent,
                    first_user_text, turns_total, bot_turns, user_turns,
                    error_count, timeout_count, handover_turn, handover_flag,
                    dead_link_turns, dead_link_count, avg_bot_chars,
                    created_at_min, created_at_max
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    session_id,
                    run_id,
                    endpoint,
                    category,
                    category_tag,
                    scenario_id,
                    scenario_label,
                    question_key,
                    variation_id,
                    persona,
                    topic,
                    intent,
                    user_turn1,
                    max(int(r.get('turn') or 0) for r in srows_sorted),
                    len(bot_rows),
                    len(user_rows),
                    error_count,
                    timeout_count,
                    handover_turn,
                    1 if handover_turn else 0,
                    dead_link_turns,
                    dead_link_count,
                    round(avg_bot_chars, 2),
                    created_at_min,
                    created_at_max,
                ),
            )

            for r in srows_sorted:
                cur.execute(
                    '''
                    INSERT INTO turns (
                        row_id, run_id, endpoint, session_id, category, category_tag,
                        scenario_id, question_key, turn, role, text, handover,
                        links_json, dead_links_json, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        int(r.get('id') or 0),
                        run_id,
                        endpoint,
                        session_id,
                        r.get('category'),
                        r.get('category_tag'),
                        scenario_id,
                        question_key,
                        int(r.get('turn') or 0),
                        r.get('role'),
                        r.get('text') or '',
                        int(r.get('handover') or 0),
                        r.get('links') or '[]',
                        r.get('dead_links') or '[]',
                        r.get('timestamp'),
                    ),
                )

    conn.commit()
    conn.close()
    print(f'Built simlab DB: {DB_PATH}')


if __name__ == '__main__':
    main()
