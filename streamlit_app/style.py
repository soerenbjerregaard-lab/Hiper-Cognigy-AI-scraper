import streamlit as st


def metric_row(metrics):
    """Render a row of custom metric cards that never truncate.
    metrics = list of (label, value) tuples.
    """
    cards = "".join(
        f'<div style="flex:1;min-width:110px;background:#f8fafc;border:1px solid #e2e8f0;'
        f'border-radius:10px;padding:0.85rem 1rem">'
        f'<div style="font-size:0.72rem;font-weight:700;color:#64748b;text-transform:uppercase;'
        f'letter-spacing:0.05em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{label}</div>'
        f'<div style="font-size:1.75rem;font-weight:700;color:#1e40af;margin-top:2px">{value}</div>'
        f'</div>'
        for label, value in metrics
    )
    return (
        f'<div style="display:flex;gap:10px;flex-wrap:wrap;margin:0.5rem 0 1rem">{cards}</div>'
    )


def meta_pills(items):
    """Compact inline metadata row. items = list of (label, value) tuples."""
    pills = "".join(
        f'<span style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:6px;'
        f'padding:3px 10px;font-size:0.82rem;color:#334155">'
        f'<b style="color:#64748b">{label}</b> {value}</span>'
        for label, value in items
    )
    return f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px">{pills}</div>'


def inject_css():
    st.markdown("""
    <style>

    /* ── Layout: full width ──────────────────────────────────────────────── */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }

    /* ── Hide Streamlit footer ───────────────────────────────────────────── */
    #MainMenu, footer { visibility: hidden; }

    /* ── Section headers ─────────────────────────────────────────────────── */
    .section-header {
        font-size: 0.73rem;
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
        max-height: 480px;
        overflow-y: auto;
        padding: 0.5rem 0.6rem;
        background: #fff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }
    .chat-meta {
        font-size: 0.71rem;
        color: #94a3b8;
        font-weight: 600;
        margin: 0.55rem 0 2px;
    }
    .chat-user {
        background: #dbeafe;
        border: 1px solid #bfdbfe;
        border-radius: 0 10px 10px 10px;
        padding: 0.5rem 0.8rem;
        font-size: 0.875rem;
        line-height: 1.5;
        max-width: 90%;
    }
    .chat-bot {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 10px 10px 10px 0;
        padding: 0.5rem 0.8rem;
        font-size: 0.875rem;
        line-height: 1.55;
        max-width: 90%;
        margin-left: auto;
    }
    .chat-bot a { color: #1e40af; }
    .handover-badge {
        display: inline-block;
        background: #fef3c7;
        border: 1px solid #fbbf24;
        border-radius: 5px;
        padding: 1px 7px;
        font-size: 0.7rem;
        color: #92400e;
        margin-top: 4px;
        float: right;
        clear: both;
    }
    .dead-link-note {
        font-size: 0.7rem;
        color: #b45309;
        margin-top: 3px;
        text-align: right;
    }

    /* ── Judge result ────────────────────────────────────────────────────── */
    .judge-ha {
        display: inline-block;
        background: #dbeafe;
        border: 1px solid #93c5fd;
        border-radius: 6px;
        padding: 2px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #1e40af;
        margin-bottom: 0.4rem;
    }
    .judge-summary {
        font-size: 0.875rem;
        color: #1e3a5f;
        line-height: 1.5;
        background: #f0fdf4;
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 0.6rem 0.9rem;
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
        border-radius: 6px;
    }

    /* ── Divider ─────────────────────────────────────────────────────────── */
    hr { border-color: #e2e8f0 !important; margin: 0.8rem 0 !important; }

    /* ── Dataframe ────────────────────────────────────────────────────────── */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    [data-testid="stDataFrame"] thead th {
        background: #f1f5f9 !important;
        font-size: 0.76rem !important;
        font-weight: 700 !important;
        color: #475569 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    </style>
    """, unsafe_allow_html=True)
