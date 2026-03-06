import streamlit as st


def inject_css():
    st.markdown("""
    <style>

    /* ── Layout: full width, less top padding ───────────────────────────── */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* ── Hide Streamlit footer ───────────────────────────────────────────── */
    #MainMenu, footer { visibility: hidden; }

    /* ── Metric cards ────────────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 0.9rem 1rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.9rem !important;
        font-weight: 700 !important;
        color: #1e40af !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        color: #64748b !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── Section headers ─────────────────────────────────────────────────── */
    .section-header {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 1rem 0 0.5rem;
        padding-bottom: 5px;
        border-bottom: 2px solid #e2e8f0;
    }

    /* ── Chat container ──────────────────────────────────────────────────── */
    .chat-wrap {
        max-height: 520px;
        overflow-y: auto;
        padding: 0.6rem;
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }
    .chat-meta {
        font-size: 0.72rem;
        color: #94a3b8;
        font-weight: 600;
        margin: 0.6rem 0 2px;
    }
    .chat-user {
        background: #dbeafe;
        border: 1px solid #bfdbfe;
        border-radius: 0 12px 12px 12px;
        padding: 0.55rem 0.9rem;
        font-size: 0.9rem;
        line-height: 1.5;
        max-width: 92%;
    }
    .chat-bot {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 12px 12px 12px 0;
        padding: 0.55rem 0.9rem;
        font-size: 0.9rem;
        line-height: 1.55;
        max-width: 92%;
        margin-left: auto;
    }
    .chat-bot a { color: #1e40af; }
    .handover-badge {
        display: inline-block;
        background: #fef3c7;
        border: 1px solid #fbbf24;
        border-radius: 5px;
        padding: 1px 8px;
        font-size: 0.72rem;
        color: #92400e;
        margin: 3px 0 0 auto;
        float: right;
    }
    .dead-link-note {
        font-size: 0.72rem;
        color: #b45309;
        margin-top: 3px;
        text-align: right;
    }

    /* ── Judge result card ───────────────────────────────────────────────── */
    .judge-box {
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-top: 0.6rem;
    }
    .judge-ha {
        display: inline-block;
        background: #dbeafe;
        border: 1px solid #93c5fd;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.5rem;
    }
    .judge-summary {
        font-size: 0.88rem;
        color: #1e3a5f;
        line-height: 1.5;
        margin-top: 0.4rem;
    }

    /* ── Sidebar dark theme ──────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: #0f172a !important;
    }
    [data-testid="stSidebar"] * {
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebarNav"] a:hover {
        background: #1e293b !important;
    }
    [data-testid="stSidebarNav"] .active {
        background: #1e40af !important;
    }
    [data-testid="stSidebarNav"] .active * {
        color: #fff !important;
    }

    /* ── Divider ─────────────────────────────────────────────────────────── */
    hr { border-color: #e2e8f0 !important; margin: 0.8rem 0 !important; }

    /* ── Dataframe ────────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    [data-testid="stDataFrame"] thead th {
        background: #f1f5f9 !important;
        font-size: 0.78rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    </style>
    """, unsafe_allow_html=True)
