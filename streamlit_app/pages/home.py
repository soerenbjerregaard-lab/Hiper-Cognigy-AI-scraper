import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css, metric_row

inject_css()

st.title("📊 Simlab Dashboard")
st.caption("Automatiseret kvalitetsanalyse af Hipers Cognigy AI-chatbot")

# ── KPI cards (custom HTML – never truncates) ─────────────────────────────────
kpis = db.get_kpis()
if kpis:
    k = kpis[0]
    st.markdown(metric_row([
        ("Kørsler",    int(k["runs"] or 0)),
        ("Sessioner",  int(k["sessions"] or 0)),
        ("Handover",   f"{k['handover_rate_pct'] or 0}%"),
        ("Fejlrate",   f"{k['session_error_rate_pct'] or 0}%"),
        ("Dead links", f"{k['dead_link_session_rate_pct'] or 0}%"),
        ("Når T4",     f"{k['reach_t4_pct'] or 0}%"),
    ]), unsafe_allow_html=True)

st.divider()

# ── Trend + endpoint summary ──────────────────────────────────────────────────
col_chart, col_ep = st.columns([2, 3])

with col_chart:
    st.markdown('<div class="section-header">Sessioner per dag</div>', unsafe_allow_html=True)
    trend = db.get_runs_over_time()
    if len(trend) > 1:
        df_trend = pd.DataFrame(trend).set_index("run_date")
        st.line_chart(df_trend["sessions"], color="#1e40af")
    elif trend:
        # Only 1 date – just show the number nicely
        t = trend[0]
        st.markdown(
            f'<div style="font-size:0.9rem;color:#475569;padding:0.5rem 0">'
            f'<b>{t["run_date"]}</b> · {t["sessions"]} sessioner fra {t["runs"]} kørsel(er)</div>',
            unsafe_allow_html=True,
        )
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
    df_rh.columns = ["Startet", "Run-ID", "Endpoint", "Sessioner",
                      "Fejl %", "Timeout %", "Dead links %", "Handover %"]
    st.dataframe(df_rh, use_container_width=True, hide_index=True)
else:
    st.info("Ingen kørsler i databasen endnu")
