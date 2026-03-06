import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css

st.set_page_config(
    page_title="Simlab – Oversigt",
    page_icon="📊",
    layout="wide",
)
inject_css()

st.title("📊 Simlab Dashboard")
st.caption("Automatiseret kvalitetsanalyse af Hipers Cognigy AI-chatbot")

# ── KPI cards ─────────────────────────────────────────────────────────────────
kpis = db.get_kpis()
if kpis:
    k = kpis[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Kørsler", int(k["runs"] or 0))
    c2.metric("Sessioner", int(k["sessions"] or 0))
    c3.metric("Handover-rate", f"{k['handover_rate_pct'] or 0}%")
    c4.metric("Fejlrate", f"{k['session_error_rate_pct'] or 0}%")
    c5.metric("Dead links", f"{k['dead_link_session_rate_pct'] or 0}%")
    c6.metric("Når turn 4", f"{k['reach_t4_pct'] or 0}%")

st.divider()

# ── Trend + endpoint ───────────────────────────────────────────────────────────
col_chart, col_ep = st.columns([2, 3])

with col_chart:
    st.markdown('<div class="section-header">Sessioner per dag</div>', unsafe_allow_html=True)
    trend = db.get_runs_over_time()
    if len(trend) > 1:
        df_trend = pd.DataFrame(trend).set_index("run_date")
        st.line_chart(df_trend["sessions"], color="#1e40af")
    elif trend:
        st.dataframe(pd.DataFrame(trend), use_container_width=True)
    else:
        st.info("Ingen data endnu")

with col_ep:
    st.markdown('<div class="section-header">Endpoint overblik</div>', unsafe_allow_html=True)
    endpoints = db.get_endpoint_summary()
    if endpoints:
        df_ep = pd.DataFrame(endpoints)
        df_ep.columns = ["Endpoint", "Sessioner", "Handover %", "Fejl %", "Dead links %", "Gns. turns"]
        st.dataframe(df_ep, use_container_width=True, hide_index=True)

st.divider()

# ── Run health ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Kørsels-sundhed</div>', unsafe_allow_html=True)
run_health = db.get_run_health()
if run_health:
    df_rh = pd.DataFrame(run_health)
    df_rh.columns = ["Startet", "Run-ID (kort)", "Endpoint", "Sessioner",
                      "Fejl %", "Timeout %", "Dead links %", "Handover %"]
    st.dataframe(df_rh, use_container_width=True, hide_index=True)
else:
    st.info("Ingen kørsler i databasen endnu")
