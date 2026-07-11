import streamlit as st
import time

# Configure the Streamlit page for a productivity SaaS feel
st.set_page_config(
    page_title="ProductPilot",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    """Injects custom CSS to achieve the dark matte, premium SaaS aesthetic."""
    st.markdown("""
        <style>
            /* Typography and Header Styling */
            .title {
                font-size: 2.25rem;
                font-weight: 700;
                color: #F3F4F6;
                margin-top: -1.5rem;
                margin-bottom: 0.25rem;
                letter-spacing: -0.025em;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            
            .subtitle {
                font-size: 1.05rem;
                color: #9CA3AF;
                font-weight: 400;
                margin-bottom: 2rem;
            }

            /* Customizing Streamlit Expander to look like subtle cards */
            div[data-testid="stExpander"] {
                border: 1px solid #252B3A !important;
                border-radius: 8px !important;
                background-color: #141925 !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
                margin-bottom: 0.75rem;
                overflow: hidden;
            }
            
            div[data-testid="stExpander"] summary {
                font-weight: 500 !important;
                color: #F3F4F6 !important;
                padding: 1rem !important;
            }
            
            div[data-testid="stExpander"] summary:hover {
                background-color: #1a2030 !important;
            }
            
            /* Input fields styling */
            .stTextArea textarea, .stSelectbox > div > div > div {
                background-color: #141925 !important;
                border: 1px solid #252B3A !important;
                color: #F3F4F6 !important;
                border-radius: 6px !important;
                font-size: 0.95rem;
            }
            
            .stTextArea textarea:focus, .stSelectbox > div > div > div:focus-within {
                border-color: #4F8CFF !important;
                box-shadow: 0 0 0 1px #4F8CFF !important;
            }
            
            /* Checkbox styling */
            .stCheckbox span {
                color: #9CA3AF !important;
            }

            /* Primary Button Styling - No oversized gradients */
            div.stButton > button[kind="primary"] {
                background-color: #4F8CFF;
                color: #ffffff;
                border: 1px solid #4F8CFF;
                border-radius: 6px;
                padding: 0.5rem 1.25rem;
                font-size: 0.95rem;
                font-weight: 500;
                transition: background-color 0.15s ease, border-color 0.15s ease;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            }
            
            div.stButton > button[kind="primary"]:hover {
                background-color: #3b74e6;
                border-color: #3b74e6;
            }
            
            /* Sidebar navigation style (simulated) */
            .sidebar-nav {
                display: flex;
                flex-direction: column;
                gap: 0.25rem;
                margin-top: 2rem;
            }
            .sidebar-nav-item {
                padding: 0.5rem 0.75rem;
                border-radius: 6px;
                color: #9CA3AF;
                font-size: 0.95rem;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.15s ease, color 0.15s ease;
            }
            .sidebar-nav-item.active {
                background-color: #1f2738;
                color: #F3F4F6;
            }
            .sidebar-nav-item:hover:not(.active) {
                background-color: #1a2030;
                color: #F3F4F6;
            }
            
            /* Empty State Container */
            .empty-state {
                text-align: center;
                padding: 4rem 2rem;
                background-color: transparent;
                border-radius: 8px;
                border: 1px dashed #252B3A;
                color: #6B7280;
                font-size: 0.95rem;
                margin-top: 1.5rem;
            }
            
            /* Horizontal Rule */
            hr {
                border-top: 1px solid #252B3A !important;
                margin: 2.5rem 0;
            }
            
            /* Remove main container top padding for tighter fit */
            .css-18e3th9 {
                padding-top: 2rem;
            }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renders the minimal sidebar navigation."""
    with st.sidebar:
        st.markdown("<div style='font-size: 1.25rem; font-weight: 600; color: #F3F4F6; margin-bottom: 0.5rem;'>ProductPilot</div>", unsafe_allow_html=True)
        
        # Professional sidebar navigation simulating a SaaS app
        st.markdown("""
            <div class="sidebar-nav">
                <div class="sidebar-nav-item active">New PRD</div>
                <div class="sidebar-nav-item">Recent Projects</div>
                <div class="sidebar-nav-item">Templates</div>
                <div class="sidebar-nav-item">Settings</div>
                <div class="sidebar-nav-item">About</div>
            </div>
        """, unsafe_allow_html=True)

def render_header():
    """Renders the main title and subtitle."""
    st.markdown('<div class="title">ProductPilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Transform product ideas into production-ready Product Requirement Documents.</div>', unsafe_allow_html=True)

def simulate_generation():
    """Simulates generating the PRD data."""
    with st.spinner("Processing requirements..."):
        time.sleep(2)
        
        st.session_state['prd_data'] = {
            "Problem Statement": "Current workflows require manual data entry across multiple disconnected platforms, leading to a 30% increase in processing time and high error rates.",
            "Business Goals": "- Reduce manual data entry time by 50%.\n- Achieve a 99% accuracy rate in data processing.\n- Target 10,000 active enterprise users by Q3.",
            "User Personas": "**Primary: Operations Manager**\nResponsible for overseeing daily workflows and requires high-level reporting.\n\n**Secondary: Data Clerk**\nExecutes daily entries and requires an optimized, low-friction interface.",
            "Features": "1. **Single Sign-On (SSO):** Integration with Okta and Azure AD.\n2. **Unified Dashboard:** Centralized view of all processing queues.\n3. **Automated Validation:** Real-time data format checking.",
            "Functional Requirements": "- The system must integrate with RESTful external APIs.\n- Support for bulk CSV uploads up to 50MB.\n- Audit logs for all data modifications.",
            "Non-Functional Requirements": "- API response times must not exceed 200ms at P95.\n- Compliance with SOC2 Type II standards.",
            "Risk Analysis": "- **Integration Delays:** Third-party API rate limits may bottleneck initial syncs.\n  *Mitigation:* Implement exponential backoff and localized queuing.\n- **User Resistance:** Current staff are heavily accustomed to legacy spreadsheets.\n  *Mitigation:* Phase rollout with mandatory hands-on training sessions."
        }
        st.session_state['prd_generated'] = True

def main():
    load_custom_css()
    render_sidebar()
    render_header()
    
    # Input Section
    idea = st.text_area(
        "Product Idea",
        placeholder="Describe the core problem you are solving, your target audience, and the proposed solution...",
        height=160,
        label_visibility="collapsed"
    )
    
    # Project Configuration
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        industry = st.selectbox(
            "Industry",
            options=["SaaS", "FinTech", "HealthTech", "EdTech", "E-commerce", "Other"]
        )
    with col2:
        project_type = st.selectbox(
            "Project Type",
            options=["SaaS", "Marketplace", "AI Tool", "Enterprise Software", "Mobile Application", "API Service", "Healthcare Platform", "Other"]
        )
    with col3:
        audience = st.selectbox(
            "Audience",
            options=["B2B", "B2C", "Internal", "Enterprise"]
        )
    with col4:
        detail_level = st.selectbox(
            "PRD Detail Level",
            options=["High-Level", "Standard", "In-Depth"],
            index=1
        )
        
    include_risk = st.checkbox("Include Risk Analysis", value=True)
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Primary action button
    if st.button("Generate PRD", type="primary"):
        if idea.strip():
            simulate_generation()
        else:
            st.warning("Please provide a product idea first.")
            
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Output Area
    if not st.session_state.get('prd_generated', False):
        # Subtle placeholder
        st.markdown("""
            <div class="empty-state">
                Ready. Enter a product idea above to generate requirements.
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 600; color: #F3F4F6; margin-bottom: 1rem;'>Document Draft</div>", unsafe_allow_html=True)
        
        data = st.session_state['prd_data']
        
        with st.expander("Problem Statement", expanded=True):
            st.markdown(data["Problem Statement"])
            
        with st.expander("Business Goals", expanded=True):
            st.markdown(data["Business Goals"])
            
        with st.expander("User Personas"):
            st.markdown(data["User Personas"])
            
        with st.expander("Features"):
            st.markdown(data["Features"])
            
        with st.expander("Functional Requirements"):
            st.markdown(data["Functional Requirements"])
            
        with st.expander("Non-Functional Requirements"):
            st.markdown(data["Non-Functional Requirements"])
            
        if include_risk:
            with st.expander("Risk Analysis"):
                st.markdown(data["Risk Analysis"])

if __name__ == "__main__":
    main()
