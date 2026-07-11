import streamlit as st
import time

# Configure page to wide layout to support the 1200-1300px custom width container
st.set_page_config(
    page_title="ProductPilot",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    """Injects custom CSS to achieve the premium, enterprise-grade SaaS matte black workspace aesthetic."""
    st.markdown("""
        <style>
            /* Main Content Container Refinements */
            .stApp {
                background-color: #0A0A0A;
                color: #F5F5F5;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }

            /* Customizing Main Content Max-Width (1250px) and padding */
            .block-container {
                max-width: 1250px !important;
                margin: 0 auto !important;
                padding-left: 4rem !important;
                padding-right: 4rem !important;
                padding-top: 3.5rem !important;
                padding-bottom: 3.5rem !important;
            }

            /* Sidebar Refinements */
            [data-testid="stSidebar"] {
                background-color: #111111 !important;
                border-right: 1px solid #2A2A2A !important;
                min-width: 240px !important;
                max-width: 240px !important;
            }
            
            .sidebar-title {
                font-size: 1.15rem;
                font-weight: 700;
                color: #F5F5F5;
                margin-bottom: 1.75rem;
                padding-left: 0.5rem;
                letter-spacing: -0.02em;
            }

            .sidebar-nav {
                display: flex;
                flex-direction: column;
                gap: 0.35rem;
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
                border: 1px solid transparent;
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

            /* Header/Branding Typography Styling */
            .logo-title {
                font-size: 4.5rem; /* ~72px */
                font-weight: 800;
                color: #F5F5F5;
                margin-bottom: 0.15rem;
                letter-spacing: -0.04em;
                line-height: 1.05;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            }

            .section-badge {
                font-size: 0.85rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: #4F8CFF;
                font-weight: 700;
                margin-bottom: 0.5rem;
                margin-top: 1rem;
            }

            .tagline {
                font-size: 1.15rem;
                color: #9E9E9E;
                font-weight: 400;
                margin-bottom: 3.5rem;
                line-height: 1.5;
            }

            /* Writing Canvas styling (Notion-like text area) */
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

            /* Project Configuration Panel (Expander) */
            div[data-testid="stExpander"] {
                background-color: transparent !important;
                border: 1px solid #2A2A2A !important;
                border-radius: 8px !important;
                margin-bottom: 1.75rem;
            }

            div[data-testid="stExpander"] summary {
                font-weight: 600 !important;
                color: #9E9E9E !important;
                font-size: 0.95rem !important;
                padding: 0.75rem 1.25rem !important;
            }

            div[data-testid="stExpander"] summary:hover {
                color: #F5F5F5 !important;
            }

            /* Configuration Inputs */
            .stSelectbox > div > div > div {
                background-color: #111111 !important;
                border: 1px solid #2A2A2A !important;
                color: #F5F5F5 !important;
                border-radius: 6px !important;
                font-size: 0.9rem !important;
                height: 38px !important;
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

            /* AI Workflow Progress Panel */
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
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
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
                letter-spacing: 0.02em;
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

            /* Structured Output Section cards */
            .prd-section {
                background-color: #171717;
                border: 1px solid #2A2A2A;
                border-radius: 10px;
                padding: 1.75rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }

            .prd-section-title {
                font-size: 1.2rem;
                font-weight: 700;
                color: #F5F5F5;
                margin-bottom: 1rem;
                border-bottom: 1px solid #2A2A2A;
                padding-bottom: 0.6rem;
                letter-spacing: -0.01em;
            }

            .prd-section-content {
                font-size: 0.95rem;
                color: #9E9E9E;
                line-height: 1.65;
            }

            /* Custom subtle spacing elements & dividers */
            hr {
                border-top: 1px solid #2A2A2A !important;
                margin: 4rem 0;
            }
        </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Renders the minimal sidebar navigation."""
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>ProductPilot</div>", unsafe_allow_html=True)
        st.markdown("""
            <div class="sidebar-nav">
                <div class="sidebar-nav-item active">New PRD</div>
                <div class="sidebar-nav-item">History</div>
                <div class="sidebar-nav-item">Templates</div>
                <div class="sidebar-nav-item">Settings</div>
            </div>
        """, unsafe_allow_html=True)

def render_header():
    """Renders the top branding and title area."""
    st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2rem;">
            <div class="section-badge">AI Product Strategy Workspace</div>
            <h1 class="logo-title">ProductPilot</h1>
            <p class="tagline">Transform rough ideas into production-ready Product Requirement Documents.</p>
        </div>
    """, unsafe_allow_html=True)

def render_progress_panel(step):
    """Renders the collaborative AI workflow progress panel cards."""
    # Step Status calculations
    s1_status = "Completed ✓" if step > 1 else "Running" if step == 1 else "Waiting"
    s1_desc = "Analyzing market opportunity and industry alignment..." if step >= 1 else "Queueing analysis workflow..."
    s1_class = "status-completed" if step > 1 else "status-running" if step == 1 else "status-waiting"

    s2_status = "Completed ✓" if step > 2 else "Running" if step == 2 else "Waiting"
    s2_desc = "Drafting features, compiling user stories, and scheduling integrations..." if step >= 2 else "Waiting for business metrics..."
    s2_class = "status-completed" if step > 2 else "status-running" if step == 2 else "status-waiting"

    s3_status = "Completed ✓" if step > 3 else "Running" if step == 3 else "Waiting"
    s3_desc = "Writing functional and non-functional requirements schema..." if step >= 3 else "Waiting for product mapping..."
    s3_class = "status-completed" if step > 3 else "status-running" if step == 3 else "status-waiting"

    st.markdown(f"""
        <div class="progress-panel">
            <div class="progress-card {s1_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="agent-title">🧠 Business Analyst</span>
                    <span class="agent-status">{s1_status}</span>
                </div>
                <div class="agent-desc">{s1_desc}</div>
            </div>
            <div class="progress-card {s2_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="agent-title">📋 Product Manager</span>
                    <span class="agent-status">{s2_status}</span>
                </div>
                <div class="agent-desc">{s2_desc}</div>
            </div>
            <div class="progress-card {s3_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="agent-title">📄 PRD Generator</span>
                    <span class="agent-status">{s3_status}</span>
                </div>
                <div class="agent-desc">{s3_desc}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def populate_prd_data():
    """Populates placeholder PRD document dataset."""
    st.session_state['prd_data'] = {
        "Problem Statement": "Current clinical communication streams lack synchronous telemetry reporting, delaying response rates for diabetic events and complicating clinical diagnosis protocols.",
        "Business Goals": "- Reduce critical diabetic response intervals by 65% within initial testing.\n- Secure integration coverage with top 3 clinical telemetry wearables in Cycle 1.\n- Minimize onboarding friction for clinical staff (target: < 10 mins).",
        "User Personas": "**Primary: Specialist Dr. Sarah**\nRequires clean telemetry history visualizers and automated threshold event logging without administrative overhead.\n\n**Secondary: Patient Patient David**\nRequires a lightweight mobile telemetry reporter syncing securely with passive wearable APIs.",
        "Features": "1. **Wearable Telemetry Sync:** Continuous glucose data integration API.\n2. **Emergency Threshold Trigger:** Direct notification relays to clinical coordinators.\n3. **Clinical Intakes Portal:** Consolidated telemetry reports with export capabilities.",
        "Functional Requirements": "- Telemetry sync intervals must maintain < 3 second lag indices.\n- Secure login must support SAML 2.0 / SSO constraints.\n- Telemetry threshold alerts must execute in high-priority threads.",
        "Non-Functional Requirements": "- **Reliability:** 99.99% critical alert dispatcher uptime.\n- **Security:** End-to-end encryption complying with HIPAA and SOC2 regulations.",
        "Risk Analysis": "- **Wearable Failure:** Data sync disconnect during clinical window.\n  *Mitigation:* Local hardware alarms notifying patients immediately to check sensor state."
    }
    st.session_state['prd_generated'] = True

def main():
    load_custom_css()
    render_sidebar()
    render_header()
    
    # Writing Canvas Input
    idea = st.text_area(
        "Product Idea",
        placeholder="What are we building today?\n\nExample: Build an AI healthcare platform that helps doctors monitor diabetic patients through wearable devices and personalized recommendations.",
        height=130,
        label_visibility="collapsed"
    )
    
    # Character Counter placed at bottom right of canvas
    char_count = len(idea)
    st.markdown(f"<div style='text-align: right; color: #6B7280; font-size: 0.8rem; margin-top: -0.65rem; margin-bottom: 1.25rem;'>{char_count} characters</div>", unsafe_allow_html=True)
    
    # Project Configuration Panel
    with st.expander("Project Configuration", expanded=False):
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
            
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Primary Create Blueprint Action
    col_left, col_mid, col_right = st.columns([1.5, 2, 1.5])
    with col_mid:
        if st.button("Create Blueprint →", type="primary"):
            if idea.strip():
                # Set generating flag and clear previous output
                st.session_state['generating'] = True
                st.session_state['prd_generated'] = False
                
                # Execute step-by-step progress panel animations
                progress_container = st.empty()
                
                with progress_container.container():
                    render_progress_panel(step=1)
                time.sleep(1.2)
                
                with progress_container.container():
                    render_progress_panel(step=2)
                time.sleep(1.5)
                
                with progress_container.container():
                    render_progress_panel(step=3)
                time.sleep(1.0)
                
                # Finish generation
                populate_prd_data()
                st.session_state['generating'] = False
                progress_container.empty()
            else:
                st.warning("Please describe your product idea first.")
                
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Document Output Section
    if st.session_state.get('generating', False):
        # Keeps progress panel visual active while finishing up layout rendering
        render_progress_panel(step=3)
    elif not st.session_state.get('prd_generated', False):
        # Muted placeholder empty state
        st.markdown("""
            <div class="empty-state">
                <span class="empty-icon">🧊</span>
                <h3>Start with a product idea.</h3>
                <p>Your generated Product Requirement Document will appear here.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 1.3rem; font-weight: 700; color: #F5F5F5; margin-bottom: 1.5rem; letter-spacing: -0.02em;'>Document Draft</div>", unsafe_allow_html=True)
        
        data = st.session_state['prd_data']
        
        sections = [
            ("🎯 Problem Statement", data["Problem Statement"]),
            ("📈 Business Goals", data["Business Goals"]),
            ("👥 User Personas", data["User Personas"]),
            ("✨ Features", data["Features"]),
            ("⚙️ Functional Requirements", data["Functional Requirements"]),
            ("🛡️ Non-Functional Requirements", data["Non-Functional Requirements"])
        ]
        
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
