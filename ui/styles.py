import streamlit as st

def load_custom_css():
    """Injects custom CSS to style the app as an enterprise product workspace."""
    st.markdown("""
        <style>
            /* Reset & Global overrides */
            .stApp {
                background-color: #0A0A0A;
                color: #F5F5F5;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }

            /* Customizing Main Content Max-Width and centering */
            .block-container {
                max-width: 1250px !important;
                margin: 0 auto !important;
                padding-left: 4rem !important;
                padding-right: 4rem !important;
                padding-top: 3.5rem !important;
                padding-bottom: 3.5rem !important;
            }

            /* Force flex parent to center children horizontally (centered layout preservation) */
            [data-testid="stMain"] {
                align-items: center !important;
                transition: all 0.25s ease-in-out !important;
            }

            /* Sidebar Refinements & Correct Collapse Behaviour */
            [data-testid="stSidebar"] {
                background-color: #111111 !important;
                border-right: 1px solid #2A2A2A !important;
                transition: min-width 0.25s, max-width 0.25s, width 0.25s !important;
            }
            
            section[data-testid="stSidebar"][aria-expanded="true"] {
                min-width: 260px !important;
                max-width: 260px !important;
            }
            
            section[data-testid="stSidebar"][aria-expanded="false"] {
                min-width: 0px !important;
                max-width: 0px !important;
                width: 0px !important;
            }
            
            .sidebar-title {
                font-size: 1.15rem;
                font-weight: 700;
                color: #F5F5F5;
                margin-bottom: 1.75rem;
                padding-left: 0.5rem;
                letter-spacing: -0.02em;
            }

            .sidebar-section-header {
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #6B7280;
                margin-top: 1.5rem;
                margin-bottom: 0.5rem;
                padding-left: 0.5rem;
                font-weight: 700;
            }

            /* Customizing Sidebar Buttons to look like flat menu lists with metadata support */
            div[data-testid="stSidebar"] div.stButton > button {
                background-color: transparent !important;
                border: 1px solid transparent !important;
                color: #9E9E9E !important;
                text-align: left !important;
                padding: 0.5rem 0.75rem !important;
                font-size: 0.9rem !important;
                font-weight: 500 !important;
                border-radius: 6px !important;
                width: 100% !important;
                display: flex;
                justify-content: flex-start;
                align-items: center;
                transition: all 0.15s ease;
                white-space: pre-line !important;
                line-height: 1.35 !important;
            }
            
            div[data-testid="stSidebar"] div.stButton > button:hover {
                background-color: #171717 !important;
                color: #F5F5F5 !important;
                border-color: #2A2A2A !important;
            }
            
            div[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
                background-color: #171717 !important;
                border: 1px solid #2A2A2A !important;
                color: #F5F5F5 !important;
            }

            /* Workspace Header / Hero Section Refinements */
            .hero-badge {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.15em;
                color: #4F8CFF;
                font-weight: 700;
                margin-bottom: 0.5rem;
                display: inline-block;
            }

            .logo-title {
                font-size: 4.5rem; /* ~72px */
                font-weight: 800;
                color: #F5F5F5;
                margin-bottom: 0.25rem;
                letter-spacing: -0.04em;
                line-height: 1.05;
            }

            .tagline {
                font-size: 1.15rem;
                color: #9E9E9E;
                font-weight: 400;
                margin-bottom: 3.5rem;
                line-height: 1.5;
            }

            /* Writing Canvas styling */
            .stTextArea textarea {
                background-color: #111111 !important;
                border: 1px solid #2A2A2A !important;
                color: #F5F5F5 !important;
                border-radius: 8px !important;
                font-size: 1.1rem !important;
                line-height: 1.6 !important;
                padding: 1.25rem !important;
                transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
                box-shadow: none !important;
            }

            .stTextArea textarea:focus {
                border-color: #4F8CFF !important;
                box-shadow: 0 0 0 1px #4F8CFF !important;
            }

            /* Canvas label formatting */
            .stTextArea label {
                font-size: 1rem !important;
                font-weight: 600 !important;
                color: #F5F5F5 !important;
                margin-bottom: 0.5rem !important;
            }

            /* Project Configuration Panel (Expander) */
            div[data-testid="stExpander"] {
                background-color: transparent !important;
                border: 1px solid #2A2A2A !important;
                border-radius: 8px !important;
                margin-bottom: 1.75rem;
            }

            div[data-testid="stExpander"] summary {
                font-weight: 600 !important;
                color: #F5F5F5 !important;
                font-size: 0.95rem !important;
                padding: 0.75rem 1.25rem !important;
            }

            div[data-testid="stExpander"] summary:hover {
                background-color: #111111 !important;
            }

            /* Configuration Inputs */
            .stSelectbox > div > div > div {
                background-color: #111111 !important;
                border: 1px solid #2A2A2A !important;
                color: #F5F5F5 !important;
                border-radius: 6px !important;
                font-size: 0.9rem !important;
            }

            .stSelectbox label {
                color: #9E9E9E !important;
                font-size: 0.85rem !important;
                font-weight: 500 !important;
                margin-bottom: 0.25rem !important;
            }

            .stCheckbox span {
                color: #9E9E9E !important;
                font-size: 0.9rem !important;
            }

            /* Primary Action Button (Create Blueprint) with Arrow Slide Animation */
            div.stButton > button[kind="primary"] {
                background-color: #4F8CFF !important;
                color: #FFFFFF !important;
                border: 1px solid #4F8CFF !important;
                border-radius: 8px !important;
                padding: 0.75rem 2rem !important;
                font-size: 1.05rem !important;
                font-weight: 600 !important;
                transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
                box-shadow: none !important;
                width: 100% !important;
            }

            div.stButton > button[kind="primary"]:hover {
                background-color: #3b74e6 !important;
                border-color: #3b74e6 !important;
                transform: translateY(-1px);
                padding-left: 2.25rem !important;
                padding-right: 1.75rem !important;
            }

            /* Suggestion Chips styling */
            .chip-container {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 0.75rem;
                margin-bottom: 2rem;
            }

            /* Select all buttons inside example columns representing chips */
            div.chip-col div.stButton > button {
                background-color: #111111 !important;
                border: 1px solid #2A2A2A !important;
                color: #9E9E9E !important;
                font-size: 0.8rem !important;
                padding: 0.35rem 0.75rem !important;
                border-radius: 16px !important;
                text-align: center !important;
                font-weight: 500 !important;
                width: 100% !important;
                transition: all 0.15s ease !important;
            }

            div.chip-col div.stButton > button:hover {
                border-color: #4F8CFF !important;
                color: #F5F5F5 !important;
                background-color: #171717 !important;
            }

            /* Empty State */
            .empty-state {
                text-align: center;
                padding: 6.5rem 2rem;
                color: #9E9E9E;
            }

            .empty-icon {
                font-size: 2.25rem;
                display: block;
                margin-bottom: 0.75rem;
                opacity: 0.3;
            }

            .empty-state h3 {
                font-size: 1.2rem;
                font-weight: 500;
                color: #F5F5F5;
                margin-bottom: 0.25rem;
            }

            .empty-state p {
                font-size: 0.95rem;
                color: #9E9E9E;
            }

            /* AI Progress Panel */
            .progress-panel {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                margin-top: 1.5rem;
                margin-bottom: 1.5rem;
            }

            .progress-card {
                background-color: #111111;
                border: 1px solid #2A2A2A;
                border-radius: 8px;
                padding: 1.25rem 1.5rem;
            }

            .progress-card.status-running {
                border-color: #4F8CFF;
                box-shadow: 0 0 12px rgba(79, 140, 255, 0.08);
            }

            .progress-card.status-completed {
                border-color: #22C55E;
            }

            .progress-card.status-waiting {
                opacity: 0.45;
            }

            .agent-title {
                font-size: 1rem;
                font-weight: 600;
                color: #F5F5F5;
            }

            .agent-status {
                font-size: 0.85rem;
                font-weight: 600;
            }

            .status-running .agent-status {
                color: #4F8CFF;
            }

            .status-completed .agent-status {
                color: #22C55E;
            }

            .status-waiting .agent-status {
                color: #9E9E9E;
            }

            .agent-desc {
                font-size: 0.85rem;
                color: #9E9E9E;
                margin-top: 0.35rem;
            }

            /* Document deliverable cards */
            .prd-section {
                background-color: #171717;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
                padding: 1.75rem;
                margin-bottom: 1.5rem;
            }

            .prd-section-title {
                font-size: 1.2rem;
                font-weight: 700;
                color: #F5F5F5;
                margin-bottom: 1rem;
                border-bottom: 1px solid #2A2A2A;
                padding-bottom: 0.6rem;
            }

            .prd-section-content {
                font-size: 0.95rem;
                color: #9E9E9E;
                line-height: 1.65;
            }

            /* Tab Style override to match matte black workspace */
            div[data-baseweb="tab-list"] {
                background-color: transparent !important;
                border-bottom: 1px solid #2A2A2A !important;
                gap: 1.5rem !important;
            }

            div[data-baseweb="tab"] {
                color: #9E9E9E !important;
                font-weight: 500 !important;
                padding: 0.75rem 0.25rem !important;
            }

            div[data-baseweb="tab"][aria-selected="true"] {
                color: #4F8CFF !important;
                border-bottom-color: #4F8CFF !important;
            }

            hr {
                border-top: 1px solid #2A2A2A !important;
                margin: 4rem 0;
            }
        </style>
    """, unsafe_allow_html=True)
