import streamlit as st

def load_custom_css():
    """Injects custom CSS to style the app as an enterprise product workspace."""
    st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            /* ── Design Tokens ─────────────────────────────────────── */
            :root {
                --bg-primary:    #0A0A0A;
                --bg-surface:    #111111;
                --bg-elevated:   #171717;
                --bg-card:       #1A1A1A;
                --border:        #222222;
                --border-hover:  #333333;
                --text-primary:  #F0F0F0;
                --text-secondary:#9E9E9E;
                --text-muted:    #6B7280;
                --accent:        #4F8CFF;
                --accent-hover:  #3B74E6;
                --success:       #22C55E;
                --warning:       #F59E0B;
                --danger:        #EF4444;
                --radius-sm:     6px;
                --radius-md:     10px;
                --radius-lg:     14px;
                --font-family:   'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }

            /* ── Reset & Global ────────────────────────────────────── */
            .stApp {
                background-color: var(--bg-primary);
                color: var(--text-primary);
                font-family: var(--font-family);
            }

            .block-container {
                max-width: 1200px !important;
                margin: 0 auto !important;
                padding: 3rem 3.5rem !important;
            }

            [data-testid="stMain"] {
                align-items: center !important;
                transition: all 0.2s ease !important;
            }

            /* ── Sidebar ───────────────────────────────────────────── */
            [data-testid="stSidebar"] {
                background-color: var(--bg-surface) !important;
                border-right: 1px solid var(--border) !important;
                transition: min-width 0.2s, max-width 0.2s, width 0.2s !important;
            }

            section[data-testid="stSidebar"][aria-expanded="true"] {
                min-width: 250px !important;
                max-width: 250px !important;
            }

            section[data-testid="stSidebar"][aria-expanded="false"] {
                min-width: 0px !important;
                max-width: 0px !important;
                width: 0px !important;
            }

            .sidebar-title {
                font-size: 1.1rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 1.5rem;
                padding-left: 0.5rem;
                letter-spacing: -0.02em;
            }

            .sidebar-section-header {
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: var(--text-muted);
                margin-top: 1.25rem;
                margin-bottom: 0.4rem;
                padding-left: 0.5rem;
                font-weight: 700;
            }

            div[data-testid="stSidebar"] div.stButton > button {
                background-color: transparent !important;
                border: 1px solid transparent !important;
                color: var(--text-secondary) !important;
                text-align: left !important;
                padding: 0.45rem 0.65rem !important;
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                border-radius: var(--radius-sm) !important;
                width: 100% !important;
                display: flex;
                justify-content: flex-start;
                align-items: center;
                transition: all 0.12s ease;
                white-space: pre-line !important;
                line-height: 1.35 !important;
            }

            div[data-testid="stSidebar"] div.stButton > button:hover {
                background-color: var(--bg-elevated) !important;
                color: var(--text-primary) !important;
                border-color: var(--border) !important;
            }

            div[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
                background-color: var(--bg-elevated) !important;
                border: 1px solid var(--border) !important;
                color: var(--text-primary) !important;
            }

            /* ── Hero ──────────────────────────────────────────────── */
            .hero-badge {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.15em;
                color: var(--accent);
                font-weight: 700;
                margin-bottom: 0.4rem;
                display: inline-block;
            }

            .logo-title {
                font-size: 4rem;
                font-weight: 800;
                color: var(--text-primary);
                margin-bottom: 0.2rem;
                letter-spacing: -0.04em;
                line-height: 1.05;
            }

            .tagline {
                font-size: 1.05rem;
                color: var(--text-secondary);
                font-weight: 400;
                margin-bottom: 3rem;
                line-height: 1.5;
            }

            /* ── Writing Canvas ────────────────────────────────────── */
            .stTextArea textarea {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                color: var(--text-primary) !important;
                border-radius: var(--radius-md) !important;
                font-size: 1rem !important;
                line-height: 1.6 !important;
                padding: 1.15rem !important;
                transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
                box-shadow: none !important;
            }

            .stTextArea textarea:focus {
                border-color: var(--accent) !important;
                box-shadow: 0 0 0 1px var(--accent) !important;
            }

            .stTextArea label {
                font-size: 0.95rem !important;
                font-weight: 600 !important;
                color: var(--text-primary) !important;
                margin-bottom: 0.35rem !important;
            }

            /* ── Expanders ─────────────────────────────────────────── */
            div[data-testid="stExpander"] {
                background-color: transparent !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-md) !important;
                margin-bottom: 1.25rem;
            }

            div[data-testid="stExpander"] summary {
                font-weight: 600 !important;
                color: var(--text-primary) !important;
                font-size: 0.9rem !important;
                padding: 0.7rem 1.1rem !important;
            }

            div[data-testid="stExpander"] summary:hover {
                background-color: var(--bg-surface) !important;
            }

            /* ── Selects ───────────────────────────────────────────── */
            .stSelectbox > div > div > div {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                color: var(--text-primary) !important;
                border-radius: var(--radius-sm) !important;
                font-size: 0.85rem !important;
            }

            .stSelectbox label {
                color: var(--text-secondary) !important;
                font-size: 0.8rem !important;
                font-weight: 500 !important;
                margin-bottom: 0.2rem !important;
            }

            .stCheckbox span {
                color: var(--text-secondary) !important;
                font-size: 0.85rem !important;
            }

            /* ── Primary Button ────────────────────────────────────── */
            div.stButton > button[kind="primary"] {
                background-color: var(--accent) !important;
                color: #FFFFFF !important;
                border: 1px solid var(--accent) !important;
                border-radius: var(--radius-md) !important;
                padding: 0.7rem 1.75rem !important;
                font-size: 0.95rem !important;
                font-weight: 600 !important;
                transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
                box-shadow: none !important;
                width: 100% !important;
            }

            div.stButton > button[kind="primary"]:hover {
                background-color: var(--accent-hover) !important;
                border-color: var(--accent-hover) !important;
                transform: translateY(-1px);
            }

            /* ── Suggestion Chips ──────────────────────────────────── */
            .chip-container {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                margin-top: 0.5rem;
                margin-bottom: 1.5rem;
            }

            div.chip-col div.stButton > button {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                color: var(--text-secondary) !important;
                font-size: 0.78rem !important;
                padding: 0.3rem 0.65rem !important;
                border-radius: 14px !important;
                text-align: center !important;
                font-weight: 500 !important;
                width: 100% !important;
                transition: all 0.12s ease !important;
            }

            div.chip-col div.stButton > button:hover {
                border-color: var(--accent) !important;
                color: var(--text-primary) !important;
                background-color: var(--bg-elevated) !important;
            }

            /* ── Empty State ───────────────────────────────────────── */
            .empty-state {
                text-align: center;
                padding: 5rem 2rem;
                color: var(--text-secondary);
            }

            .empty-icon {
                font-size: 2rem;
                display: block;
                margin-bottom: 0.6rem;
                opacity: 0.25;
            }

            .empty-state h3 {
                font-size: 1.1rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.2rem;
            }

            .empty-state p {
                font-size: 0.88rem;
                color: var(--text-secondary);
                max-width: 400px;
                margin: 0 auto;
            }

            /* ── Step Progress Pipeline ────────────────────────────── */
            .pipeline-step {
                display: flex;
                align-items: center;
                gap: 0.6rem;
                padding: 0.5rem 0;
                font-size: 0.88rem;
                font-weight: 500;
                color: var(--text-muted);
                transition: color 0.2s ease;
            }

            .pipeline-step.done {
                color: var(--success);
            }

            .pipeline-step.running {
                color: var(--accent);
            }

            .pipeline-step .step-icon {
                font-size: 0.9rem;
                width: 1.2rem;
                text-align: center;
            }

            /* ── Document Cards ────────────────────────────────────── */
            .prd-section {
                background-color: var(--bg-elevated);
                border: 1px solid var(--border);
                border-radius: var(--radius-md);
                padding: 1.5rem;
                margin-bottom: 1.25rem;
            }

            .prd-section-title {
                font-size: 1.1rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-bottom: 0.75rem;
                border-bottom: 1px solid var(--border);
                padding-bottom: 0.5rem;
            }

            .prd-section-content {
                font-size: 0.9rem;
                color: var(--text-secondary);
                line-height: 1.65;
            }

            /* ── Tabs ──────────────────────────────────────────────── */
            div[data-baseweb="tab-list"] {
                background-color: transparent !important;
                border-bottom: 1px solid var(--border) !important;
                gap: 1.25rem !important;
            }

            div[data-baseweb="tab"] {
                color: var(--text-secondary) !important;
                font-weight: 500 !important;
                padding: 0.65rem 0.2rem !important;
                font-size: 0.88rem !important;
            }

            div[data-baseweb="tab"][aria-selected="true"] {
                color: var(--accent) !important;
                border-bottom-color: var(--accent) !important;
            }

            /* ── Metric Card ───────────────────────────────────────── */
            .metric-card {
                background-color: var(--bg-card);
                padding: 1.1rem 1.25rem;
                border-radius: var(--radius-md);
                border: 1px solid var(--border);
            }
            .metric-card .label {
                font-size: 0.7rem;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-weight: 600;
            }
            .metric-card .value {
                font-size: 1.5rem;
                font-weight: 700;
                color: var(--text-primary);
                margin-top: 0.35rem;
                line-height: 1.2;
            }
            .metric-card .subtitle {
                font-size: 0.78rem;
                color: var(--text-muted);
                margin-top: 0.2rem;
            }

            /* ── Knowledge File List ───────────────────────────────── */
            .knowledge-file {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.35rem 0;
                font-size: 0.82rem;
                color: var(--text-secondary);
            }
            .knowledge-file .file-icon {
                color: var(--text-muted);
                font-size: 0.75rem;
            }

            /* ── Horizontal Rule ───────────────────────────────────── */
            hr {
                border-top: 1px solid var(--border) !important;
                margin: 3rem 0;
            }

            /* ── Streamlit spinner override ─────────────────────────── */
            .stSpinner > div {
                border-top-color: var(--accent) !important;
            }
        </style>
    """, unsafe_allow_html=True)
