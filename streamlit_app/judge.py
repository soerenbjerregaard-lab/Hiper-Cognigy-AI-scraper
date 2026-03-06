import json
import os
import requests
from pathlib import Path
import db

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
PROMPT_VERSION = "v1"
PROMPT_PATH = Path(__file__).parent / "judge_prompt_v1.txt"


def read_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def build_transcript(turns):
    return "\n\n".join(
        f"Turn {t['turn']} [{t['role'].upper()}]: {t['text']}"
        for t in turns
    )


def _normalize_num(val, fallback=0.0):
    try:
        n = float(val)
        return n if n == n else fallback  # NaN guard
    except (TypeError, ValueError):
        return fallback


def normalize_judge(raw):
    valid_handovers = {"correct", "unnecessary", "missing", "n/a"}
    ha = raw.get("handover_assessment", "n/a")
    return {
        "response_quality":            max(1.0, min(5.0, _normalize_num(raw.get("response_quality"), 1.0))),
        "context_coherence":           max(1.0, min(5.0, _normalize_num(raw.get("context_coherence"), 1.0))),
        "helpfulness":                 max(1.0, min(5.0, _normalize_num(raw.get("helpfulness"), 1.0))),
        "handover_assessment":         ha if ha in valid_handovers else "n/a",
        "handover_should_have_happened": 1 if _normalize_num(raw.get("handover_should_have_happened")) > 0 else 0,
        "handover_unnecessary":        1 if _normalize_num(raw.get("handover_unnecessary")) > 0 else 0,
        "dead_links_found":            max(0, int(_normalize_num(raw.get("dead_links_found"), 0))),
        "summary":                     str(raw.get("summary") or "")[:300],
        "analysis_notes":              str(raw.get("analysis_notes") or "")[:600],
        "confidence":                  max(0.0, min(1.0, _normalize_num(raw.get("confidence"), 0.5))),
        "inconclusive_reason":         str(raw.get("inconclusive_reason") or "")[:300],
    }


def _call_ollama(prompt):
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
        timeout=600,
    )
    resp.raise_for_status()
    data = resp.json()
    parsed = json.loads(data["response"])
    return normalize_judge(parsed)


def run_judge(session_id):
    turns = db.get_turns_for_judge(session_id)
    if not turns:
        raise ValueError(f"Ingen turns fundet for session: {session_id}")

    transcript = build_transcript(turns)
    prompt = read_prompt().replace("{{TRANSCRIPT}}", transcript)

    # Try with one retry
    try:
        result = _call_ollama(prompt)
    except Exception:
        result = _call_ollama(prompt)

    run_id = db.get_session_run_id(session_id)
    db.save_judgement(session_id, run_id, PROMPT_VERSION, OLLAMA_MODEL, result)
    return result
