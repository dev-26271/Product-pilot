import streamlit as st
import time

# Configure page to center content and set the document title
st.set_page_config(
    page_title="ProductPilot",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    """Injects custom CSS to achieve the matte black, premium SaaS workspace aesthetic."""
    st.markdown("""
        <style>
            /* Reset & Global overrides */
            .stApp {
                background-color: #0A0A0A;
                color: #F5F5F5;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }

            /* Sidebar Customization */
            [data-testid="stSidebar"] {
                background-color: #111111 !important;
                border-right: 1px solid #2A2A2A !important;
            }
            
            .sidebar-title {
                font-size: 1.1rem;
                font-weight: 600;
                color: #F5F5F5;
                margin-bottom: 1.5rem;
                padding-left: 0.5rem;
                letter-spacing: -0.01em;
            }

            .sidebar-nav {
                display: flex;
                flex-direction: column;
                gap: 0.25rem;
                margin-top: 1rem;
            }

            .sidebar-nav-item {
                padding: 0.5rem 0.75rem;
                border-radius: 6px;
                color: #9E9E9E;
                font-size: 0.9rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.15s ease;
                text-decoration: none;
            }

            .sidebar-nav-item.active {
                background-color: #171717;
                color: #F5F5F5;
                border: 1px solid #2A2A2A;
            }

            .sidebar-nav-item:hover:not(.active) {
                background-color: #171717;
                color: #F5F5F5;
            }

            /* Header Section */
            .logo-title {
                font-size: 4.5rem;
                font-weight: 800;
                color: #F5F5F5;
                margin-bottom: 0rem;
                letter-spacing: -0.04em;
                line-height: 1.1;
            }

            .section-badge {
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.15em;
                color: #4F8CFF;
                font-weight: 600;
                margin-bottom: 0.5rem;
                margin-top: 1rem;
            }

            .tagline {
                font-size: 1.1rem;
                color: #9E9E9E;
                font-weight: 400;
                margin-bottom: 3rem;
                line-height: 1.5;
            }

            /* Writing Canvas - Notion style borderless feel */
            .stTextArea textarea {
                background-color: #111111 !important;
                border: 1px solid #2A2A2A !important;
                color: #F5F5F5 !important;
                border-radius: 8px !important;
                font-size: 1.1rem !important;
                line-height: 1.6 !important;
                padding: 1.5rem !important;
                transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
                box-shadow: none !important;
            }

            .stTextArea textarea:focus {
                border-color: #4F8CFF !important;
                box-shadow: 0 0 0 1px #4F8CFF !important;
            }

            /* Collapsible Advanced Settings (Expander) */
            div[data-testid="stExpander"] {
                background-color: transparent !important;
                border: 1px solid #2A2A2A !important;
                border-radius: 6px !important;
                margin-bottom: 1.5rem;
            }

            div[data-testid="stExpander"] summary {
                font-weight: 500 !important;
                color: #9E9E9E !important;
                font-size: 0.9rem !important;
                padding: 0.75rem 1rem !important;
            }

            div[data-testid="stExpander"] summary:hover {
                color: #F5F5F5 !important;
            }

            /* Form Element Layout Overrides */
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

            /* Primary Action Button (Create Blueprint) */
            div.stButton > button[kind="primary"] {
                background-color: #4F8CFF !important;
                color: #FFFFFF !important;
                border: 1px solid #4F8CFF !important;
                border-radius: 6px !important;
                padding: 0.6rem 2rem !important;
                font-size: 1rem !important;
                font-weight: 500 !important;
                transition: background-color 0.15s ease, transform 0.1s ease !important;
                box-shadow: none !important;
            }

            div.stButton > button[kind="primary"]:hover {
                background-color: #3b74e6 !important;
                border-color: #3b74e6 !important;
            }

            /* Empty State styling */
            .empty-state {
                text-align: center;
                padding: 5rem 2rem;
                color: #9E9E9E;
            }

            .empty-icon {
                font-size: 2rem;
                display: block;
                margin-bottom: 0.75rem;
                opacity: 0.4;
            }

            .empty-state h3 {
                font-size: 1.15rem;
                font-weight: 500;
                color: #F5F5F5;
                margin-bottom: 0.25rem;
            }

            .empty-state p {
                font-size: 0.9rem;
                color: #9E9E9E;
            }

            /* Flat PRD Card Layout */
            .prd-section {
                background-color: #171717;
                border: 1px solid #2A2A2A;
                border-radius: 8px;
                padding: 1.5rem;
                margin-bottom: 1.25rem;
            }

            .prd-section-title {
                font-size: 1.15rem;
                font-weight: 600;
                color: #F5F5F5;
                margin-bottom: 0.75rem;
                border-bottom: 1px solid #2A2A2A;
                padding-bottom: 0.5rem;
            }

            .prd-section-content {
                font-size: 0.95rem;
                color: #9E9E9E;
                line-height: 1.6;
            }

            /* Thin Dividers */
            hr {
                border-top: 1px solid #2A2A2A !important;
                margin: 3.5rem 0;
            }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renders the minimal, product-focused sidebar navigation."""
    with st.sidebar:
        st.markdown("<div class="sidebar-title">ProductPilot</div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="sidebar-nav">
                <div class="sidebar-nav-item active">New PRD</div>
                <div class="sidebar-nav-item">History</div>
                <div class="sidebar-nav-item">Templates</div>
                <div class="sidebar-nav-item">Settings</div>
            </div>
        """, unsafe_allow_html=True)

def render_header():
    """Renders the clean, elegant headline typography."""
    st.markdown("""
        <div style="text-align: center; margin-top: 2rem; margin-bottom: 1.5rem;">
            <div class="section-badge">Your AI Product Team</div>
            <h1 class="logo-title">ProductPilot</h1>
            <p class="tagline">Turn rough ideas into production-ready Product Requirement Documents.</p>
        </div>
    """, unsafe_allow_html=True)

def simulate_generation():
    """Simulates generating the PRD blueprint."""
    with st.spinner("Processing requirements..."):
        time.sleep(2.5)
        
        st.session_state['prd_data'] = {
            "Problem Statement": "Current healthcare platforms fail to connect patients with clinical specialists in real-time, resulting in diagnostic delays and fragmented patient intake workflows.",
            "Business Goals": "- Reduce average scheduling time from 4 days to less than 15 minutes.\n- Establish active connections with 1,000+ board-certified physicians in the first cycle.\n- Achieve patient satisfaction score (CSAT) of 92% or higher.",
            "User Personas": "**Primary: Patient Patient Paul**\nRequires prompt, structured clinical advice without navigating administrative hurdles.\n\n**Secondary: Specialist Specialist Dana**\nDemands streamlined patient triage information and digital prescription capabilities.",
            "Features": "1. **Structured Intake Engine:** Guided workflow capturing symptoms.\n2. **Specialist Matcher:** Algorithm routing based on clinical profiles.\n3. **Real-time Consult Portal:** Encrypted interface with synchronized medical records.",
            "Functional Requirements": "- Data transmission must use secure end-to-end TLS 1.3 protocol.\n- Sync profiles within 1.5 seconds across both physician and patient clients.\n- Support attachment uploads up to 10MB.",
            "Non-Functional Requirements": "- **SLA:** 99.95% system availability.\n- **Regulatory:** SOC2 Type II and HIPAA compliant infrastructure.",
            "Risk Analysis": "- **Clinical Compliance:** Misrouting patients requiring emergency care.\n  *Mitigation:* Pre-intake filter identifying emergency indicators and redirecting to 911.\n- **Data Security:** Exposure of Protected Health Information (PHI).\n  *Mitigation:* Row-level encryption database structures and strict audit logs."
        }
        st.session_state['prd_generated'] = True

def main():
    load_custom_css()
    render_sidebar()
    render_header()
    
    # Writing Canvas (Notion-like)
    idea = st.text_area(
        "Product Idea",
        placeholder="What are we building today?\n\nExample: Build an AI healthcare platform that connects patients with doctors and provides personalized treatment recommendations.",
        height=180,
        label_visibility="collapsed"
    )
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Advanced Settings (Collapsible)
    with st.expander("Advanced Settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            industry = st.selectbox(
                "Industry",
                options=["Healthcare", "Finance", "Education", "Retail", "Logistics", "Travel", "Real Estate", "HR", "Legal", "Entertainment", "Government", "Other"]
            )
        with col2:
            product_type = st.selectbox(
                "Product Type",
                options=["SaaS Platform", "Mobile App", "AI Assistant", "Marketplace", "Dashboard", "Internal Tool", "API Platform", "Enterprise Software", "CRM", "Productivity Tool"]
            )
        with col3:
            audience = st.selectbox(
                "Audience",
                options=["B2B", "B2C", "Enterprise", "Internal", "Government"]
            )
            
        col4, col5 = st.columns([1, 1])
        with col4:
            prd_depth = st.selectbox(
                "PRD Depth",
                options=["Basic", "Standard", "Comprehensive"],
                index=1
            )
        with col5:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
            include_risk = st.checkbox("Include Risk Analysis", value=True)
            
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Centered Primary Action Button
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        if st.button("Create Blueprint →", type="primary", use_container_width=True):
            if idea.strip():
                simulate_generation()
            else:
                st.warning("Please provide a product idea first.")
                
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Output Area
    if not st.session_state.get('prd_generated', False):
        # Muted placeholder
        st.markdown("""
            <div class="empty-state">
                <span class="empty-icon">🧊</span>
                <h3>Start with a product idea.</h3>
                <p>Your generated Product Requirement Document will appear here.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 1.25rem; font-weight: 700; color: #F5F5F5; margin-bottom: 1.5rem; letter-spacing: -0.02em;'>Document Draft</div>", unsafe_allow_html=True)
        
        data = st.session_state['prd_data']
        
        # Displaying generated PRD using styled container classes instead of default Streamlit cards
        sections = [
            ("🎯 Problem Statement", data["Problem Statement"]),
            ("📈 Business Goals", data["Business Goals"]),
            ("👥 User Personas", data["User Personas"]),
            ("✨ Features", data["Features"]),
            ("⚙️ Functional Requirements", data["Functional Requirements"]),
            ("🛡️ Non-Functional Requirements", data["Non-Functional Requirements"])
        ]
        
        # Add risk if selected
        if include_risk and "Risk Analysis" in data:
            sections.append(("⚠️ Risk Analysis", data["Risk Analysis"]))
            
        for title, content in sections:
            st.markdown(f"""
                <div class="prd-section">
                    <div class="prd-section-title">{title}</div>
                    <div class="prd-section-content">{content.replace(chr(10), '<br>')}</div>
                </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
