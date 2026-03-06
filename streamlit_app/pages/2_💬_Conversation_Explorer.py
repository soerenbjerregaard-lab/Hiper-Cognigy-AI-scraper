import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
import judge as judge_module
from style import inject_css, metric_row

inject_css()


def render_chat(turns):
    if not turns:
        st.info("Ingen samtale at vise")
        return

    parts = ['<div class="chat-wrap">']
    for t in turns:
        role     = t["role"]
        text     = str(t.get("text") or "")
        turn_num = t["turn"]
        handover = t.get("handover", 0)
        dead     = t.get("dead_links_json", "")

        label = "Bruger" if role == "user" else "Bot"
        parts.append(f'<div class="chat-meta">{label} · T{turn_num}</div>')
        css   = "chat-user" if role == "user" else "chat-bot"
        parts.append(f'<div class="{css}">{text}')
        if handover and role != "user":
            parts.append('<span class="handover-badge">🔀 Handover</span>')
        if dead and dead not in ("[]", "null", "", "None"):
            parts.append(f'<div class="dead-link-note">⚠️ Dead links: {dead}</div>')
        parts.append('</div>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("💬 Samtaleudforsker")
st.caption("Udforsk individuelle samtaler og kør AI Judge")

# ── Filters full-width at top ─────────────────────────────────────────────────
runs       = db.get_run_options()
run_labels = ["— Alle kørsler —"] + [r["label"] for r in runs]
run_ids    = [None] + [r["run_id"] for r in runs]

fc1, fc2 = st.columns([1, 2])
with fc1:
    sel_run = st.selectbox("Kørsel", run_labels)
    selected_run_id = run_ids[run_labels.index(sel_run)]

sessions    = db.get_sessions_for_run(selected_run_id)
sess_labels = ["— Vælg samtale —"] + [s["label"] for s in sessions]
sess_ids    = [None] + [s["session_id"] for s in sessions]

with fc2:
    sel_sess   = st.selectbox("Samtale", sess_labels)
    session_id = sess_ids[sess_labels.index(sel_sess)]

st.divider()

if not session_id:
    st.info("Vælg en samtale i filtrene ovenfor")
    st.stop()

# ── Metadata ──────────────────────────────────────────────────────────────────
meta = db.get_session_meta(session_id)
if meta:
    m = meta[0]
    st.markdown(metric_row([
        ("Turns",      m["turns_total"]),
        ("Handover",   "✅ Ja" if m["handover_flag"] else "Nej"),
        ("Fejl",       m["error_count"]),
        ("Dead links", m["dead_link_count"]),
        ("Gns. chars", int(m["avg_bot_chars"] or 0)),
    ]), unsafe_allow_html=True)
    st.caption(f"Kørsel: {m['run_started_at']}  ·  Endpoint: {m['endpoint']}")

# ── Samtale ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Samtale</div>', unsafe_allow_html=True)
render_chat(db.get_conversation(session_id))

st.divider()

# ── AI Judge ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">AI Judge</div>', unsafe_allow_html=True)
judge_key = f"judge_{session_id}"

if st.button("🤖 Kør AI Judge på denne samtale", use_container_width=True):
    with st.spinner("Kalder Qwen via Ollama… (15–45 sek)"):
        try:
            result = judge_module.run_judge(session_id)
            st.session_state[judge_key] = {"ok": True, "data": result}
        except Exception as e:
            st.session_state[judge_key] = {"ok": False, "error": str(e)}

if judge_key in st.session_state:
    cached = st.session_state[judge_key]
    if cached["ok"]:
        r = cached["data"]
        st.markdown(metric_row([
            ("Svar-kvalitet", f"{r['response_quality']:.1f}/5"),
            ("Kontekst",      f"{r['context_coherence']:.1f}/5"),
            ("Hjælpsomhed",   f"{r['helpfulness']:.1f}/5"),
            ("Confidence",    f"{r['confidence']:.2f}"),
        ]), unsafe_allow_html=True)
        st.markdown(
            f'<div class="judge-ha">Handover: {r["handover_assessment"]}</div>',
            unsafe_allow_html=True,
        )
        if r.get("summary"):
            st.markdown(f'<div class="judge-summary">{r["summary"]}</div>', unsafe_allow_html=True)
        if r.get("analysis_notes"):
            with st.expander("📝 Detaljerede noter"):
                st.write(r["analysis_notes"])
    else:
        st.error(f"Fejl fra AI Judge: {cached['error']}")

# ── Judge history ─────────────────────────────────────────────────────────────
history = db.get_judge_history(session_id)
if history:
    st.divider()
    st.markdown('<div class="section-header">Tidligere vurderinger</div>', unsafe_allow_html=True)
    df_h = pd.DataFrame(history)
    df_h.columns = ["Tidspunkt", "Prompt", "Model", "Svar", "Kontekst",
                     "Hjælp", "Handover", "Conf.", "Sammenfatning"]
    st.dataframe(df_h, use_container_width=True, hide_index=True)
