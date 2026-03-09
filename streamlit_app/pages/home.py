import sys
import os
import subprocess
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import db
from style import inject_css, metric_row, signal_color, progress_bar_html

inject_css()

PROJECT_ROOT = Path(__file__).parent.parent.parent  # streamlit_app/pages/ → project root

# ── Header + run-trigger knap ─────────────────────────────────────────────────
_hdr, _btn = st.columns([5, 1])
with _hdr:
    st.title("📊 Chatbot-kvalitet")
    st.caption("Automatiseret kvalitetsanalyse af Hipers Cognigy AI-chatbot")
with _btn:
    st.markdown("<div style='height:1.3rem'></div>", unsafe_allow_html=True)
    if st.button("▶ Ny kørsel", type="primary", use_container_width=True):
        proc = subprocess.Popen(
            ["node", "run.js"],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        st.session_state["_run_pid"] = proc.pid
        st.session_state["_run_at"]  = time.strftime("%H:%M")
        st.rerun()

if "_run_pid" in st.session_state:
    pid = st.session_state["_run_pid"]
    try:
        os.kill(pid, 0)   # signal 0 = tjek om processen eksisterer (dræber ikke)
        running = True
    except (ProcessLookupError, PermissionError):
        running = False
    if running:
        st.info(f"⏳ Kørsel kører siden {st.session_state['_run_at']} — opdater siden om et par minutter")
    else:
        _sc1, _sc2 = st.columns([5, 1])
        _sc1.success(f"✅ Kørsel færdig (startet {st.session_state['_run_at']}) — data nedenfor er opdateret")
        if _sc2.button("OK", key="_run_ack"):
            del st.session_state["_run_pid"]
            del st.session_state["_run_at"]
            st.rerun()

# ── Intro for nye brugere ─────────────────────────────────────────────────────
with st.expander("ℹ️ Hvad viser dette dashboard?"):
    st.markdown("""
**Kort fortalt:** Vi sender automatisk test-spørgsmål til Hipers chatbot og måler hvor godt den svarer.

- **En kørsel** = én test-runde, hvor alle scenarier sendes til chatten parallelt
- **En session** = én samtale (spørgsmål + opfølgning) med chatbotten
- **Handover** = chatten sender kunden videre til et menneske. Høj rate → botten kan ikke selv svare
- **Handover i åbningstid** = handover under en kørsel i tidsrummet 8–16, hvor kundeservice er åben (reel handover)
- **Handover udenfor timer** = handover under en kørsel uden for åbningstiden — teknisk set sker det, men kunden når ingen reel agent
- **Dead links** = links i bot-svar der ikke virker (404-fejl, forkerte URL'er)
- **Fejlrate** = sessioner hvor noget gik teknisk galt (timeout, ingen svar)
- **4+ ture** = samtaler hvor kunden stillede opfølgningsspørgsmål (tegn på engageret dialog)
- **Endpoint** = den specifikke chatbot-konfiguration der blev testet

**Farvekoder:** <span style="color:#16a34a;font-weight:700">Grøn</span> = godt · <span style="color:#d97706;font-weight:700">Gul</span> = opmærksom · <span style="color:#dc2626;font-weight:700">Rød</span> = kritisk

Brug sidemenuen til at dykke ned i specifikke samtaler og sammenligne scenarier.
""", unsafe_allow_html=True)

# ── KPI cards (color-coded) ───────────────────────────────────────────────────
kpis = db.get_kpis()
if kpis:
    k = kpis[0]
    error_val    = float(k['session_error_rate_pct'] or 0)
    deadlink_val = float(k['dead_link_session_rate_pct'] or 0)
    t4_val       = float(k['reach_t4_pct'] or 0)

    # Business hours handover split
    _hours_map = {r["period"]: float(r["handover_rate_pct"] or 0)
                  for r in (db.get_handover_by_hours() or [])}
    ho_in  = _hours_map.get("in_hours",     float(k['handover_rate_pct'] or 0))
    ho_out = _hours_map.get("out_of_hours", float(k['handover_rate_pct'] or 0))

    # Health score baseret på åbningstids-handover (mere meningsfuld)
    health = max(0, min(100, round(100 - ho_in * 0.5 - error_val * 2 - deadlink_val * 1.5)))
    health_color = signal_color(health, (70, 40), low_is_good=False)

    # Build explanation of what pulls the score down
    drivers = []
    if ho_in > 50:
        drivers.append(f"høj handover i åbningstid ({ho_in}%)")
    elif ho_in > 20:
        drivers.append(f"forhøjet handover i åbningstid ({ho_in}%)")
    if error_val > 15:
        drivers.append(f"høj fejlrate ({error_val}%)")
    elif error_val > 5:
        drivers.append(f"forhøjet fejlrate ({error_val}%)")
    if deadlink_val > 15:
        drivers.append(f"mange døde links ({deadlink_val}%)")
    elif deadlink_val > 5:
        drivers.append(f"forhøjede døde links ({deadlink_val}%)")
    driver_text = "Primære problemer: " + ", ".join(drivers) if drivers else "Ingen kritiske problemer fundet"

    st.markdown(
        f'<div style="display:flex;align-items:center;gap:1rem;margin:0 0 0.8rem">'
        f'<div style="font-size:2.5rem;font-weight:800;color:{health_color}">{health}</div>'
        f'<div>'
        f'<div style="font-size:0.85rem;font-weight:700;color:#475569">Samlet sundhedsscore</div>'
        f'<div style="font-size:0.75rem;color:#94a3b8">0–100 · Baseret på fejl, handover i åbningstid og døde links</div>'
        f'<div style="font-size:0.75rem;color:#64748b;margin-top:2px">{driver_text}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    bh = f"{db.BUSINESS_HOURS_START}–{db.BUSINESS_HOURS_END}"
    st.markdown(metric_row([
        ("Kørsler",              int(k["runs"] or 0),
         "#1e40af", "Antal test-runder der er blevet kørt"),
        ("Sessioner",            int(k["sessions"] or 0),
         "#1e40af", "Antal individuelle samtaler med chatbotten"),
        (f"Handover ({bh})",     f"{ho_in}%",
         signal_color(ho_in, (20, 50), low_is_good=True),
         f"Handover-rate for kørsler i åbningstiden ({bh}). Disse handovers er reelle — kunden kan nå en agent."),
        ("Handover (udenfor)",   f"{ho_out}%",
         "#94a3b8",
         "Handover-rate for kørsler udenfor åbningstid. Kunden kan ikke nå en reel agent — brug kun som teknisk reference."),
        ("Fejlrate",             f"{error_val}%",
         signal_color(error_val, (5, 15), low_is_good=True),
         "Andel sessioner med tekniske fejl (timeout, tomt svar)"),
        ("Dead links",           f"{deadlink_val}%",
         signal_color(deadlink_val, (5, 15), low_is_good=True),
         "Andel sessioner med ødelagte links i bot-svar"),
        ("4+ ture",              f"{t4_val}%",
         signal_color(t4_val, (60, 30), low_is_good=False),
         "Samtaler med 4+ beskeder. Høj = engagerede samtaler"),
    ]), unsafe_allow_html=True)

st.divider()

# ── Indsigt 1: Kategori-performance ──────────────────────────────────────────
col_cat, col_timing = st.columns([3, 2])

with col_cat:
    st.markdown('<div class="section-header">Handover-rate per emneområde</div>', unsafe_allow_html=True)
    st.caption("Hvilken type kundespørgsmål er chatbotten dårligst til at håndtere?")
    cats = db.get_category_summary()
    if cats:
        parts = []
        for c in cats:
            ho = float(c["handover_pct"] or 0)
            col = signal_color(ho, (20, 50), low_is_good=True)
            bar_pct = min(round(ho), 100)
            parts.append(
                f'<div style="display:flex;align-items:center;gap:0.6rem;margin:0.3rem 0;'
                f'padding:0.45rem 0.75rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px">'
                f'<div style="flex:1;font-size:0.84rem;font-weight:600;color:#0f172a">{c["category"]}</div>'
                f'<div style="font-size:0.72rem;color:#94a3b8;min-width:5rem;text-align:right">'
                f'{c["sessions"]} sess. · {c["avg_turns"]} ture</div>'
                f'<div style="display:flex;align-items:center;gap:0.4rem;min-width:80px">'
                f'{progress_bar_html(bar_pct, col)}'
                f'<div style="font-size:0.9rem;font-weight:700;color:{col};min-width:2.5rem;text-align:right">{ho}%</div>'
                f'</div></div>'
            )
        st.markdown("".join(parts), unsafe_allow_html=True)
    else:
        st.info("Ingen kategoridata endnu")

with col_timing:
    st.markdown('<div class="section-header">Hvornår sker handover?</div>', unsafe_allow_html=True)
    st.caption("Giver botten op straks, eller efter forsøg?")
    dist = db.get_handover_turn_distribution()
    if dist:
        total_ho = sum(d["sessions"] for d in dist)
        labels = {
            1: ("Tur 1 – straks",   "Botten kan slet ikke hjælpe",     "#dc2626"),
            2: ("Tur 2 – tidligt",  "Botten prøvede én gang og gav op", "#d97706"),
        }
        for d in dist:
            turn = d["handover_turn"]
            pct  = round(d["sessions"] / total_ho * 100) if total_ho else 0
            if turn <= 2:
                label, sub, col = labels.get(turn, (f"Tur {turn}", "", "#64748b"))
            else:
                label, sub, col = "Tur 3+ – sent", "Prøvede længe, men fejlede", "#d97706"
            st.markdown(
                f'<div style="padding:0.5rem 0.75rem;margin:0.3rem 0;background:#f8fafc;'
                f'border-left:4px solid {col};border-radius:0 8px 8px 0">'
                f'<div style="font-size:0.84rem;font-weight:700;color:{col}">'
                f'{label} · {pct}% ({d["sessions"]} sess.)</div>'
                f'<div style="font-size:0.72rem;color:#64748b;margin-top:1px">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Ingen handover-data endnu")

st.divider()

# ── Indsigt 2: AI-dommer aggregat ────────────────────────────────────────────
agg = db.get_judge_aggregate()
if agg and agg.get("judged_sessions"):
    st.markdown('<div class="section-header">AI-dommer: Samlet kvalitetsvurdering</div>', unsafe_allow_html=True)
    st.caption(f"Baseret på {agg['judged_sessions']} bedømte samtaler")

    q_col  = signal_color(float(agg["avg_quality"] or 0),    (3.5, 2.5), low_is_good=False)
    h_col  = signal_color(float(agg["avg_helpfulness"] or 0),(3.5, 2.5), low_is_good=False)
    c_col  = signal_color(float(agg["avg_context"] or 0),    (3.5, 2.5), low_is_good=False)

    st.markdown(metric_row([
        ("Gns. svarkvalitet",   f"{agg['avg_quality']}/5",     q_col,
         "Gennemsnit af AI-dommerens svarkvalitetsscore. 1=ubrugelig, 5=perfekt"),
        ("Gns. hjælpsomhed",    f"{agg['avg_helpfulness']}/5", h_col,
         "Løser botten typisk kundens problem?"),
        ("Gns. kontekstscore",  f"{agg['avg_context']}/5",     c_col,
         "Husker botten typisk hvad der er sagt tidligere?"),
        ("Unødv. handover",     f"{agg['unnecessary_handover_pct'] or 0}%", "#d97706",
         "Andel samtaler hvor botten sendte videre, men burde selv have svaret"),
        ("Manglende handover",  f"{agg['missing_handover_pct'] or 0}%",    "#dc2626",
         "Andel samtaler hvor botten BURDE have sendt videre, men ikke gjorde det"),
    ]), unsafe_allow_html=True)

    # Quality trend if multiple runs judged
    trend_data = db.get_quality_trend_by_run()
    if len(trend_data) > 1:
        st.markdown('<div class="section-header">Kvalitetstrend per kørsel</div>', unsafe_allow_html=True)
        st.caption("Stiger den gennemsnitlige AI-dommer score mellem kørsler?")
        df_qt = pd.DataFrame(trend_data).set_index("run_started_at")[
            ["avg_quality", "avg_helpfulness", "avg_context"]
        ]
        df_qt.columns = ["Svarkvalitet", "Hjælpsomhed", "Kontekst"]
        st.line_chart(df_qt)

    st.divider()

# ── Indsigt 3: Top 5 problematiske spørgsmål ─────────────────────────────────
st.markdown('<div class="section-header">Top 5 – Spørgsmål med højeste handover-rate</div>', unsafe_allow_html=True)
st.caption("Start din analyse her – åbn disse i Spørgsmålsanalyse for at se detaljerne")
top_q = db.get_top_handover_questions(5)
if top_q:
    parts = []
    for i, q in enumerate(top_q, 1):
        ho = float(q["handover_rate_pct"] or 0)
        bar_color = signal_color(ho, (20, 50), low_is_good=True)
        bar_pct = min(round(ho), 100)
        parts.append(
            f'<div style="display:flex;align-items:center;gap:0.75rem;margin:0.4rem 0;padding:0.5rem 0.75rem;'
            f'background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px">'
            f'<div style="font-size:0.78rem;font-weight:700;color:#94a3b8;min-width:1.2rem">{i}.</div>'
            f'<div style="flex:1;min-width:0">'
            f'<div style="font-size:0.85rem;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
            f'{q["question_text"]}</div>'
            f'<div style="font-size:0.72rem;color:#64748b">{q["category"]} · {q["sessions"]} sessioner</div>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:0.5rem;min-width:90px">'
            f'{progress_bar_html(bar_pct, bar_color)}'
            f'<div style="font-size:0.95rem;font-weight:700;color:{bar_color}">{ho}%</div>'
            f'</div>'
            f'</div>'
        )
    st.markdown("".join(parts), unsafe_allow_html=True)

st.divider()

# ── Kørsels-sundhed (teknisk overblik) ────────────────────────────────────────
st.markdown('<div class="section-header">Kørsels-sundhed</div>', unsafe_allow_html=True)
st.caption("Teknisk oversigt per test-kørsel – lav fejl- og handover-rate er bedst")
run_health = db.get_run_health()
if run_health:
    df_rh = pd.DataFrame(run_health)
    df_rh.columns = ["Startet", "Kørsel", "Endpoint", "Sessioner",
                      "Fejl %", "Timeout %", "Døde links %", "Handover %", "Åbningstid?"]
    st.dataframe(df_rh, use_container_width=True, hide_index=True)
else:
    st.info("Ingen kørsler i databasen endnu")
