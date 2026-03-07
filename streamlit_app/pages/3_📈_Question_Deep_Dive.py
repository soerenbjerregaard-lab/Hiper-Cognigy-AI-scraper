import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css, metric_row, signal_color

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

st.title("📈 Spørgsmålsanalyse")
st.caption("Analysér ét spørgsmål på tværs af alle test-kørsler – se om svarkvaliteten ændrer sig over tid")

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
    ho_val = float(ov['handover_rate_pct'] or 0)
    er_val = float(ov['error_rate_pct'] or 0)
    st.markdown(metric_row([
        ("Sessioner",    ov["sessions"],            "#1e40af", "Antal test-samtaler for dette spørgsmål"),
        ("Handover",     f"{ho_val}%",
         signal_color(ho_val, (20, 50), low_is_good=True),
         "Andel samtaler sendt videre til menneske"),
        ("Fejlrate",     f"{er_val}%",
         signal_color(er_val, (5, 15), low_is_good=True),
         "Andel samtaler med tekniske fejl"),
        ("Gns. ture",    ov["avg_turns"],           "#1e40af", "Gennemsnitligt antal beskeder i samtalen"),
    ]), unsafe_allow_html=True)

st.divider()

left_col, right_col = st.columns([3, 2], gap="large")

with left_col:
    st.markdown('<div class="section-header">Resultat per kørsel</div>', unsafe_allow_html=True)
    by_run = db.get_question_by_run(question_key)
    if by_run:
        df_run = pd.DataFrame(by_run)
        df_run.columns = ["Startet", "Endpoint", "Sessioner", "Handover %",
                           "Fejl %", "Døde links %", "Gns. ture"]
        st.dataframe(df_run, use_container_width=True, hide_index=True)

        if len(by_run) > 1:
            st.markdown('<div class="section-header">Handover-rate over tid</div>', unsafe_allow_html=True)
            st.caption("Faldende kurve = botten bliver bedre til at svare selv")
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
                ("Ture",        m["turns_total"],
                 "#1e40af", "Antal beskeder i samtalen"),
                ("Handover",    "✅ Ja" if m["handover_flag"] else "Nej",
                 "#dc2626" if m["handover_flag"] else "#16a34a",
                 "Kunden sendt videre til et menneske"),
                ("Døde links",  m["dead_link_count"],
                 "#dc2626" if m["dead_link_count"] else "#16a34a",
                 "Ødelagte links i bot-svar"),
            ]), unsafe_allow_html=True)
        render_chat(db.get_conversation(session_id))
