import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css, signal_color, progress_bar_html

inject_css()

st.title("🔗 Døde links")
st.caption("Links i bot-svar der ikke virker — 404-fejl, forkerte URL'er eller andre fejl")

# ── Hent data ─────────────────────────────────────────────────────────────────
urls    = db.get_dead_link_urls()
by_cat  = db.get_dead_links_by_category()
by_run  = db.get_dead_links_by_run()

if not urls:
    st.info("Ingen døde links fundet i databasen endnu.")
    st.stop()

# ── KPI-kort ──────────────────────────────────────────────────────────────────
total_hits     = sum(u["hits"]     for u in urls)
total_sessions = sum(u["sessions"] for u in urls)
unique_urls    = len(urls)

c1, c2, c3 = st.columns(3)
c1.metric("Unikke døde URL'er",   unique_urls)
c2.metric("Total antal hits",     total_hits,     help="Gange et dødt link optræder i alle bot-svar")
c3.metric("Berørte sessioner",    total_sessions, help="Samtaler hvor mindst ét dødt link blev leveret")

st.divider()

# ── Top URL'er ─────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<div class="section-header">Hyppigste døde links</div>', unsafe_allow_html=True)
    st.caption("Sorteret efter antal gange URL'en optræder i bot-svar")

    max_hits = urls[0]["hits"] if urls else 1
    parts = []
    for u in urls:
        pct = min(round(u["hits"] / max_hits * 100), 100)
        col = "#dc2626" if u["hits"] >= 10 else "#d97706" if u["hits"] >= 3 else "#64748b"
        # Vis kun sti-delen for at spare plads
        display = u["url"].replace("https://www.hiper.dk", "").replace("https://hiper.dk", "")
        display = display or u["url"]
        parts.append(
            f'<div style="margin:0.3rem 0;padding:0.5rem 0.75rem;background:#f8fafc;'
            f'border:1px solid #e2e8f0;border-radius:8px">'
            f'<div style="display:flex;align-items:center;gap:0.6rem">'
            f'{progress_bar_html(pct, col, width_px=80, height_px=6)}'
            f'<span style="font-size:0.95rem;font-weight:700;color:{col};min-width:2rem">'
            f'{u["hits"]}</span>'
            f'<span style="font-size:0.78rem;color:#475569;word-break:break-all">{display}</span>'
            f'</div>'
            f'<div style="font-size:0.7rem;color:#94a3b8;margin-top:3px">'
            f'{u["sessions"]} sess. · <a href="{u["url"]}" target="_blank" '
            f'style="color:#3b82f6;text-decoration:none">{u["url"]}</a></div>'
            f'</div>'
        )
    st.markdown("".join(parts), unsafe_allow_html=True)

# ── Per emneområde ────────────────────────────────────────────────────────────
with col_right:
    st.markdown('<div class="section-header">Berørte emneområder</div>', unsafe_allow_html=True)
    st.caption("Hvilke kategorier har flest sessioner med ødelagte links?")

    if by_cat:
        max_sess = by_cat[0]["sessions_with_deadlinks"]
        parts = []
        for c in by_cat:
            s = c["sessions_with_deadlinks"]
            pct = min(round(s / max_sess * 100), 100) if max_sess else 0
            col = signal_color(s, (5, 10), low_is_good=True)
            parts.append(
                f'<div style="display:flex;align-items:center;gap:0.6rem;margin:0.3rem 0;'
                f'padding:0.45rem 0.75rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px">'
                f'<div style="flex:1;font-size:0.84rem;font-weight:600;color:#0f172a">{c["category"]}</div>'
                f'<div style="font-size:0.72rem;color:#94a3b8;white-space:nowrap">'
                f'{c["unique_urls"]} URL · {c["total_hits"]} hits</div>'
                f'<div style="display:flex;align-items:center;gap:0.4rem;min-width:70px">'
                f'{progress_bar_html(pct, col)}'
                f'<div style="font-size:0.9rem;font-weight:700;color:{col};min-width:1.5rem;text-align:right">{s}</div>'
                f'</div></div>'
            )
        st.markdown("".join(parts), unsafe_allow_html=True)

st.divider()

# ── Per kørsel ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Udvikling per kørsel</div>', unsafe_allow_html=True)
st.caption("Er antallet af døde links faldende over tid?")

if by_run:
    df_run = pd.DataFrame(by_run)
    df_run.columns = ["Startet", "Endpoint", "Sessioner m. dead links", "Unikke URL'er", "Total hits"]
    st.dataframe(df_run, use_container_width=True, hide_index=True)

    if len(by_run) > 1:
        df_chart = pd.DataFrame(by_run).set_index("run_started_at")[["total_hits", "unique_urls"]]
        df_chart.columns = ["Total hits", "Unikke URL'er"]
        st.line_chart(df_chart)
else:
    st.info("Kun én kørsel — ingen trenddata endnu")

st.divider()

# ── Fuld URL-tabel (ekspanderbar) ─────────────────────────────────────────────
with st.expander(f"📋 Alle {unique_urls} døde URL'er (tabel)"):
    df_urls = pd.DataFrame(urls)
    df_urls.columns = ["URL", "Hits", "Sessioner"]
    st.dataframe(df_urls, use_container_width=True, hide_index=True)
