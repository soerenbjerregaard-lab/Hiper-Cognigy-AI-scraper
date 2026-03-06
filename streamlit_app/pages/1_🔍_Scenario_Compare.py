import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import judge as judge_module
from style import inject_css

st.set_page_config(
    page_title="Scenario Compare",
    page_icon="🔍",
    layout="wide",
)
inject_css()


# ── Helpers ───────────────────────────────────────────────────────────────────

def render_chat(turns):
    """Render conversation turns as styled chat bubbles."""
    if not turns:
        st.markdown(
            '<div style="color:#94a3b8;font-style:italic;padding:1rem 0">'
            'Ingen samtale tilgængelig</div>',
            unsafe_allow_html=True,
        )
        return

    parts = ['<div class="chat-wrap">']
    for t in turns:
        role = t["role"]
        text = str(t.get("text") or "")
        turn_num = t["turn"]
        handover = t.get("handover", 0)
        dead = t.get("dead_links_json", "")

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


def render_judge_result(r):
    """Display a judge result dict as native Streamlit widgets."""
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Svar-kvalitet", f"{r['response_quality']:.1f} / 5")
    sc2.metric("Kontekst", f"{r['context_coherence']:.1f} / 5")
    sc3.metric("Hjælpsomhed", f"{r['helpfulness']:.1f} / 5")
    sc4.metric("Confidence", f"{r['confidence']:.2f}")

    ha = r.get("handover_assessment", "n/a")
    st.markdown(
        f'<div class="judge-ha">Handover: {ha}</div>',
        unsafe_allow_html=True,
    )
    if r.get("summary"):
        st.markdown(
            f'<div class="judge-summary">{r["summary"]}</div>',
            unsafe_allow_html=True,
        )
    if r.get("analysis_notes"):
        with st.expander("📝 Detaljerede noter"):
            st.write(r["analysis_notes"])


def render_column(col_label, session_id):
    """Render one full comparison column."""
    st.markdown(f'<div class="section-header">{col_label}</div>', unsafe_allow_html=True)

    if not session_id:
        st.markdown(
            '<div style="color:#94a3b8;font-style:italic;padding:1rem 0">Ingen session valgt</div>',
            unsafe_allow_html=True,
        )
        return

    # Session metadata
    meta = db.get_session_meta(session_id)
    if meta:
        m = meta[0]
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Turns", m["turns_total"])
        mc2.metric("Handover", "✅ Ja" if m["handover_flag"] else "Nej")
        mc3.metric("Dead links", m["dead_link_count"])

    # Chat
    turns = db.get_conversation(session_id)
    render_chat(turns)

    st.markdown("")  # spacer

    # AI Judge button
    judge_key = f"judge_{session_id}"
    if st.button("🤖 Kør AI Judge", key=f"btn_{session_id}", use_container_width=True):
        with st.spinner("Kalder Qwen via Ollama…"):
            try:
                result = judge_module.run_judge(session_id)
                st.session_state[judge_key] = {"ok": True, "data": result}
            except Exception as e:
                st.session_state[judge_key] = {"ok": False, "error": str(e)}

    # Show result (from this run or cached from session state)
    if judge_key in st.session_state:
        cached = st.session_state[judge_key]
        if cached["ok"]:
            render_judge_result(cached["data"])
        else:
            st.error(f"Fejl: {cached['error']}")
    else:
        # Show latest saved result from DB if available
        latest = db.get_latest_judge(session_id)
        if latest:
            st.caption(f"Seneste vurdering: {latest['judged_at']}")
            render_judge_result(latest)


# ── Page ──────────────────────────────────────────────────────────────────────

st.title("🔍 Scenario Compare")
st.caption("Sammenlign op til 3 simuleringer side om side for det samme spørgsmål")

# Topic dropdown
topics = db.get_topic_options()
topic_labels = [t["label"] for t in topics]
topic_keys   = [t["question_key"] for t in topics]

sel_topic = st.selectbox(
    "Spørgsmål / scenarie",
    options=["— Vælg spørgsmål —"] + topic_labels,
    key="topic_sel",
)

if sel_topic == "— Vælg spørgsmål —":
    st.info("Vælg et spørgsmål ovenfor for at starte sammenligningen")
    st.stop()

question_key = topic_keys[topic_labels.index(sel_topic)]

# Clear cached judge results when topic changes
if st.session_state.get("_last_topic") != question_key:
    for k in [k for k in st.session_state if k.startswith("judge_")]:
        del st.session_state[k]
    st.session_state["_last_topic"] = question_key

# Load sessions + defaults
sessions = db.get_session_options(question_key)
defaults = db.get_default_sessions(question_key)

if not sessions:
    st.warning("Ingen sessioner fundet for dette spørgsmål")
    st.stop()

session_ids    = [s["session_id"] for s in sessions]
session_labels = [s["label"] for s in sessions]
session_map    = dict(zip(session_ids, session_labels))

# Map slot → default index
default_by_slot = {int(d["slot"]): d["session_id"] for d in defaults}


def default_idx(slot):
    sid = default_by_slot.get(slot)
    if sid and sid in session_ids:
        return session_ids.index(sid)
    return min(slot - 1, len(session_ids) - 1)


st.divider()

# Session selectors
dc1, dc2, dc3 = st.columns(3)
with dc1:
    session_a = st.selectbox(
        "Simulation A", options=session_ids, index=default_idx(1),
        format_func=lambda s: session_map.get(s, s), key="sel_a",
    )
with dc2:
    session_b = st.selectbox(
        "Simulation B", options=session_ids, index=default_idx(2),
        format_func=lambda s: session_map.get(s, s), key="sel_b",
    )
with dc3:
    session_c = st.selectbox(
        "Simulation C", options=session_ids, index=default_idx(3),
        format_func=lambda s: session_map.get(s, s), key="sel_c",
    )

st.divider()

# Comparison columns
col_a, col_b, col_c = st.columns(3)
with col_a:
    render_column("Simulation A", session_a)
with col_b:
    render_column("Simulation B", session_b)
with col_c:
    render_column("Simulation C", session_c)
