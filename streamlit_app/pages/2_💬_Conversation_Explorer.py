import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
import judge as judge_module
from style import inject_css

st.set_page_config(
    page_title="Samtaleudforsker",
    page_icon="💬",
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
        handover = t.get("handover", 0)
        dead     = t.get("dead_links_json", "")

        parts.append(f'<div class="chat-meta">{"Bruger" if role=="user" else "Bot"} · T{turn_num}</div>')
        bubble_class = "chat-user" if role == "user" else "chat-bot"
        parts.append(f'<div class="{bubble_class}">{text}')

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

left, right = st.columns([1, 2], gap="large")

with left:
    st.markdown('<div class="section-header">Filter</div>', unsafe_allow_html=True)

    runs = db.get_run_options()
    run_labels = ["— Alle kørsler —"] + [r["label"] for r in runs]
    run_ids    = [None] + [r["run_id"] for r in runs]

    sel_run = st.selectbox("Kørsel", run_labels)
    selected_run_id = run_ids[run_labels.index(sel_run)]

    sessions = db.get_sessions_for_run(selected_run_id)
    sess_labels = ["— Vælg samtale —"] + [s["label"] for s in sessions]
    sess_ids    = [None] + [s["session_id"] for s in sessions]

    sel_sess = st.selectbox("Samtale", sess_labels)
    session_id = sess_ids[sess_labels.index(sel_sess)]

with right:
    if not session_id:
        st.info("Vælg en samtale i venstre panel")
        st.stop()

    # Metadata
    meta = db.get_session_meta(session_id)
    if meta:
        m = meta[0]
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Turns", m["turns_total"])
        mc2.metric("Handover", "✅ Ja" if m["handover_flag"] else "Nej")
        mc3.metric("Fejl", m["error_count"])
        mc4.metric("Dead links", m["dead_link_count"])
        st.caption(f"Kørsel: {m['run_started_at']}  ·  Endpoint: {m['endpoint']}")

    st.divider()

    # Chat log
    st.markdown('<div class="section-header">Samtale</div>', unsafe_allow_html=True)
    turns = db.get_conversation(session_id)
    render_chat(turns)

    st.divider()

    # AI Judge
    st.markdown('<div class="section-header">AI Judge</div>', unsafe_allow_html=True)
    judge_key = f"judge_{session_id}"

    if st.button("🤖 Kør AI Judge på denne samtale", use_container_width=True):
        with st.spinner("Kalder Qwen via Ollama… (kan tage 15–45 sek)"):
            try:
                result = judge_module.run_judge(session_id)
                st.session_state[judge_key] = {"ok": True, "data": result}
            except Exception as e:
                st.session_state[judge_key] = {"ok": False, "error": str(e)}

    # Display result
    if judge_key in st.session_state:
        cached = st.session_state[judge_key]
        if cached["ok"]:
            r = cached["data"]
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("Svar-kvalitet", f"{r['response_quality']:.1f} / 5")
            sc2.metric("Kontekst", f"{r['context_coherence']:.1f} / 5")
            sc3.metric("Hjælpsomhed", f"{r['helpfulness']:.1f} / 5")
            sc4.metric("Confidence", f"{r['confidence']:.2f}")
            st.markdown(
                f'<div class="judge-ha">Handover: {r["handover_assessment"]}</div>',
                unsafe_allow_html=True,
            )
            if r.get("summary"):
                st.info(r["summary"])
            if r.get("analysis_notes"):
                with st.expander("📝 Detaljerede noter"):
                    st.write(r["analysis_notes"])
        else:
            st.error(f"Fejl fra AI Judge: {cached['error']}")

    # Show previous runs from DB
    history = db.get_judge_history(session_id)
    if history:
        st.divider()
        st.markdown('<div class="section-header">Tidligere AI Judge vurderinger</div>', unsafe_allow_html=True)
        df_h = pd.DataFrame(history)
        df_h.columns = ["Tidspunkt", "Prompt ver.", "Model", "Svar-kval.", "Kontekst",
                         "Hjælpsomhed", "Handover", "Confidence", "Sammenfatning"]
        st.dataframe(df_h, use_container_width=True, hide_index=True)
