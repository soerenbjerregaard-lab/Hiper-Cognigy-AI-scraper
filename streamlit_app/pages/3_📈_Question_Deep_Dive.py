import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css, metric_row

inject_css()


def render_chat(turns):
    if not turns:
        st.info("Ingen samtale at vise")
        return
    parts = ['<div class="chat-wrap">']
    for t in turns:
        role, text, turn_num = t["role"], str(t.get("text") or ""), t["turn"]
        label = "Bruger" if role == "user" else "Bot"
        parts.append(f'<div class="chat-meta">{label} · T{turn_num}</div>')
        css = "chat-user" if role == "user" else "chat-bot"
        parts.append(f'<div class="{css}">{text}</div>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("📈 Deep Dive")
st.caption("Analysér ét spørgsmål på tværs af alle kørsler")

questions = db.get_question_options()
q_labels  = [q["label"] for q in questions]
q_keys    = [q["question_key"] for q in questions]

sel_q = st.selectbox("Spørgsmål", ["— Vælg spørgsmål —"] + q_labels)

if sel_q == "— Vælg spørgsmål —":
    st.info("Vælg et spørgsmål ovenfor")
    st.stop()

question_key = q_keys[q_labels.index(sel_q)]

overview = db.get_question_overview(question_key)
if overview:
    ov = overview[0]
    st.markdown(f"**Spørgsmål:** {ov['question_text']}")
    st.markdown(f"**Kategori:** `{ov['category']}`")
    st.markdown(metric_row([
        ("Sessioner",  ov["sessions"]),
        ("Handover",   f"{ov['handover_rate_pct']}%"),
        ("Fejlrate",   f"{ov['error_rate_pct']}%"),
        ("Gns. turns", ov["avg_turns"]),
    ]), unsafe_allow_html=True)

st.divider()

left_col, right_col = st.columns([3, 2], gap="large")

with left_col:
    st.markdown('<div class="section-header">Performance per kørsel</div>', unsafe_allow_html=True)
    by_run = db.get_question_by_run(question_key)
    if by_run:
        df_run = pd.DataFrame(by_run)
        df_run.columns = ["Startet", "Endpoint", "Sessioner", "Handover %",
                           "Fejl %", "Dead links %", "Gns. turns"]
        st.dataframe(df_run, use_container_width=True, hide_index=True)

        if len(by_run) > 1:
            st.markdown('<div class="section-header">Handover-trend</div>', unsafe_allow_html=True)
            st.line_chart(
                pd.DataFrame(by_run).set_index("run_started_at")["handover_rate_pct"],
                color="#1e40af",
            )

with right_col:
    st.markdown('<div class="section-header">Kig på specifik samtale</div>', unsafe_allow_html=True)
    sessions    = db.get_session_options(question_key)
    sess_labels = ["— Vælg samtale —"] + [s["label"] for s in sessions]
    sess_ids    = [None] + [s["session_id"] for s in sessions]

    sel_s      = st.selectbox("Samtale", sess_labels, key="q_session_sel")
    session_id = sess_ids[sess_labels.index(sel_s)]

    if session_id:
        meta = db.get_session_meta(session_id)
        if meta:
            m = meta[0]
            st.markdown(metric_row([
                ("Turns",    m["turns_total"]),
                ("Handover", "✅" if m["handover_flag"] else "—"),
                ("Links",    m["dead_link_count"]),
            ]), unsafe_allow_html=True)
        render_chat(db.get_conversation(session_id))
