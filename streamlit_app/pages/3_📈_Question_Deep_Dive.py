import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css

st.set_page_config(
    page_title="Question Deep Dive",
    page_icon="📈",
    layout="wide",
)
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
        parts.append(f'<div class="chat-meta">{"Bruger" if role=="user" else "Bot"} · T{turn_num}</div>')
        bubble_class = "chat-user" if role == "user" else "chat-bot"
        parts.append(f'<div class="{bubble_class}">{text}</div>')
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("📈 Spørgsmål Deep Dive")
st.caption("Analysér et enkelt spørgsmål på tværs af alle kørsler")

# Question selector
questions = db.get_question_options()
q_labels  = [q["label"] for q in questions]
q_keys    = [q["question_key"] for q in questions]

sel_q = st.selectbox(
    "Spørgsmål",
    options=["— Vælg spørgsmål —"] + q_labels,
)

if sel_q == "— Vælg spørgsmål —":
    st.info("Vælg et spørgsmål ovenfor")
    st.stop()

question_key = q_keys[q_labels.index(sel_q)]

# Overview stats
overview = db.get_question_overview(question_key)
if overview:
    ov = overview[0]
    st.markdown(f"**Spørgsmål:** {ov['question_text']}")
    st.markdown(f"**Kategori:** `{ov['category']}`")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sessioner i alt", ov["sessions"])
    c2.metric("Handover-rate", f"{ov['handover_rate_pct']}%")
    c3.metric("Fejlrate", f"{ov['error_rate_pct']}%")
    c4.metric("Gns. turns", ov["avg_turns"])

st.divider()

# Per-run table + trend left, session drill-down right
left_col, right_col = st.columns([3, 2], gap="large")

with left_col:
    st.markdown('<div class="section-header">Performance per kørsel</div>', unsafe_allow_html=True)
    by_run = db.get_question_by_run(question_key)
    if by_run:
        df_run = pd.DataFrame(by_run)
        df_run.columns = ["Startet", "Endpoint", "Sessioner", "Handover %", "Fejl %", "Dead links %", "Gns. turns"]
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

    sel_s = st.selectbox("Samtale", sess_labels, key="q_session_sel")
    session_id = sess_ids[sess_labels.index(sel_s)]

    if session_id:
        meta = db.get_session_meta(session_id)
        if meta:
            m = meta[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Turns", m["turns_total"])
            m2.metric("Handover", "✅ Ja" if m["handover_flag"] else "Nej")
            m3.metric("Dead links", m["dead_link_count"])

        turns = db.get_conversation(session_id)
        render_chat(turns)
