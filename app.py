import streamlit as st
import time

# Configure page to wide layout for the enterprise workspace width
st.set_page_config(
    page_title="ProductPilot Workspace",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Pre-populate Mock Project Database to simulate a persistent product workspace
if 'projects' not in st.session_state:
    st.session_state['projects'] = {
        "Healthcare AI": {
            "name": "Healthcare AI",
            "idea": "An AI healthcare platform that helps doctors monitor diabetic patients through wearable devices and personalized recommendations.",
            "industry": "Healthcare",
            "product_type": "Mobile Application",
            "audience": "B2C",
            "deliverables": {
                "Product Requirements Document (PRD)": {
                    "content": {
                        "🎯 Problem Statement": "Patients with chronic conditions like diabetes lack real-time continuous feedback from clinical teams, causing delayed response times during glycemic events.",
                        "📈 Business Goals": "- Reduce critical diabetic response intervals by 65% within initial testing.\n- Establish active connections with 1,000+ board-certified physicians in the first cycle.\n- Achieve patient satisfaction score (CSAT) of 92% or higher.",
                        "👥 User Personas": "**Primary: Dr. Sarah**\nRequires clean telemetry history visualizers and automated threshold event logging.\n\n**Secondary: Patient David**\nRequires a lightweight mobile telemetry reporter syncing securely with passive wearable APIs.",
                        "✨ Features": "1. **Wearable Telemetry Sync:** Continuous glucose data integration API.\n2. **Emergency Threshold Trigger:** Direct notification relays to clinical coordinators.\n3. **Clinical Intakes Portal:** Consolidated telemetry reports with export capabilities."
                    }
                },
                "User Stories": {
                    "content": {
                        "📖 Patient Stories": "- *As a patient, I want my glucose levels to sync automatically so I don't have to enter them manually.*\n- *As a patient, I want an alert when my glucose levels are dangerously high so I can take immediate action.*",
                        "📖 Doctor Stories": "- *As a doctor, I want to see a patient's historical trends in a single dashboard so I can make informed adjustments to their plan.*"
                    }
                },
                "Product Roadmap": {
                    "content": {
                        "🗓️ Phase 1 (Q3 2026)": "- Core Telemetry API Integration\n- Patient iOS/Android App Launch (Beta)\n- Direct Messaging Service",
                        "🗓️ Phase 2 (Q4 2026)": "- Hospital EHR System Integration (HL7/FHIR)\n- Predictive Risk Analytics Dashboard"
                    }
                }
            }
        },
        "Food Delivery Platform": {
            "name": "Food Delivery Platform",
            "idea": "A hyper-local food delivery marketplace optimized for eco-friendly drone shipping and zero-waste packaging.",
            "industry": "Retail",
            "product_type": "Marketplace",
            "audience": "B2C",
            "deliverables": {
                "Executive Summary": {
                    "content": {
                        "🎯 Vision": "Establish the world's first carbon-neutral, hyper-local food logistics framework using automated drone delivery nodes.",
                        "📈 Market Opportunity": "Demand for green delivery options has surged by 180% year-over-year in metropolitan test areas."
                    }
                }
            }
        },
        "CRM SaaS": {
            "name": "CRM SaaS",
            "idea": "A privacy-first CRM SaaS designed for security-conscious enterprise teams with local-first syncing and end-to-end encryption.",
            "industry": "Finance",
            "product_type": "SaaS Platform",
            "audience": "Enterprise",
            "deliverables": {}
        },
        "Student Assistant": {
            "name": "Student Assistant",
            "idea": "An offline-first study companion utilizing localized LLMs for private research, summarizing, and flashcard generation.",
            "industry": "Education",
            "product_type": "Productivity Tool",
            "audience": "B2B",
            "deliverables": {}
        }
    }
    st.session_state['active_project_id'] = None # "New Project" mode by default

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
            }

            /* Sidebar Customization */
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

            /* Customizing Sidebar Buttons to look like flat menu lists */
            div[data-testid="stSidebar"] div.stButton > button {
                background-color: transparent !important;
                border: 1px solid transparent !important;
                color: #9E9E9E !important;
                text-align: left !important;
                padding: 0.45rem 0.75rem !important;
                font-size: 0.9rem !important;
                font-weight: 500 !important;
                border-radius: 6px !important;
                width: 100% !important;
                display: flex;
                justify-content: flex-start;
                align-items: center;
                transition: all 0.15s ease;
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

            /* Workspace Header typography */
            .logo-title {
                font-size: 4.5rem;
                font-weight: 800;
                color: #F5F5F5;
                margin-bottom: 0.15rem;
                letter-spacing: -0.04em;
                line-height: 1.05;
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

            /* Action Buttons (Flat Blue) */
            div.stButton > button[kind="primary"] {
                background-color: #4F8CFF !important;
                color: #FFFFFF !important;
                border: 1px solid #4F8CFF !important;
                border-radius: 8px !important;
                padding: 0.75rem 2rem !important;
                font-size: 1.05rem !important;
                font-weight: 600 !important;
                transition: all 0.2s ease !important;
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

def render_sidebar():
    """Renders the workspace sidebar with persistent projects lists."""
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>ProductPilot</div>", unsafe_allow_html=True)
        
        # New Project Action
        if st.button("＋ New Project", key="new_proj_btn", use_container_width=True, type="secondary"):
            st.session_state['active_project_id'] = None
            st.rerun()
            
        # Projects Section
        st.markdown("<div class='sidebar-section-header'>Projects</div>", unsafe_allow_html=True)
        for proj_name in st.session_state['projects'].keys():
            is_active = st.session_state['active_project_id'] == proj_name
            # Render standard buttons styled by CSS to look like custom list items
            if st.button(
                f"📁 {proj_name}", 
                key=f"proj_{proj_name}", 
                use_container_width=True, 
                type="primary" if is_active else "secondary"
            ):
                st.session_state['active_project_id'] = proj_name
                st.rerun()
                
        # Footer Action links
        st.markdown("<div class='sidebar-section-header'>Workspace Settings</div>", unsafe_allow_html=True)
        st.button("⚙️ Settings", key="settings_btn", use_container_width=True)
        st.button("📚 Templates", key="templates_btn", use_container_width=True)

def render_header():
    """Renders the top branding header."""
    st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2.5rem;">
            <div class="section-badge">AI Product Strategy Workspace</div>
            <h1 class="logo-title">ProductPilot</h1>
            <p class="tagline">Transform rough ideas into production-ready product documentation.</p>
        </div>
    """, unsafe_allow_html=True)

def render_progress_panel(step, deliverable_name="Product Requirements Document (PRD)"):
    """Renders progress states when compilation workflow executes."""
    s1_status = "Completed ✓" if step > 1 else "Running" if step == 1 else "Waiting"
    s1_desc = f"Mapping specifications for {deliverable_name}..." if step >= 1 else "Queueing mapping engine..."
    s1_class = "status-completed" if step > 1 else "status-running" if step == 1 else "status-waiting"

    s2_status = "Completed ✓" if step > 2 else "Running" if step == 2 else "Waiting"
    s2_desc = "Compiling document sections and aligning metadata parameters..." if step >= 2 else "Waiting for base specifications..."
    s2_class = "status-completed" if step > 2 else "status-running" if step == 2 else "status-waiting"

    s3_status = "Completed ✓" if step > 3 else "Running" if step == 3 else "Waiting"
    s3_desc = "Structuring Markdown models and exporting artifacts..." if step >= 3 else "Waiting for drafting cycles..."
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

def simulate_new_project_generation(idea, industry, product_type, audience, deliverable, include_risk):
    """Simulates creating and compiling a new project."""
    with st.spinner("Initializing Project..."):
        # Simulated multi-agent assembly
        progress_container = st.empty()
        with progress_container.container():
            render_progress_panel(step=1, deliverable_name=deliverable)
        time.sleep(1.2)
        
        with progress_container.container():
            render_progress_panel(step=2, deliverable_name=deliverable)
        time.sleep(1.5)
        
        with progress_container.container():
            render_progress_panel(step=3, deliverable_name=deliverable)
        time.sleep(1.0)
        
        # Derive a project name
        proj_name = " ".join(idea.split()[:2]) + " Project"
        
        # Populate Mock Document Data
        mock_content = {
            "🎯 Executive Summary": f"Comprehensive roadmap and architectural specs focused on {idea}.",
            "📈 Business Vision": f"Targeting {audience} audience segments inside the {industry} industry.",
            "⚙️ Technical Setup": f"Deploying custom infrastructure for a {product_type} model."
        }
        
        if include_risk:
            mock_content["⚠️ Risk Factors"] = "Initial sync intervals and compatibility vectors."

        # Add to state database
        st.session_state['projects'][proj_name] = {
            "name": proj_name,
            "idea": idea,
            "industry": industry,
            "product_type": product_type,
            "audience": audience,
            "deliverables": {
                deliverable: {
                    "content": mock_content
                }
            }
        }
        st.session_state['active_project_id'] = proj_name
        progress_container.empty()

def main():
    load_custom_css()
    render_sidebar()
    
    active_id = st.session_state.get('active_project_id', None)
    
    if active_id is None:
        # ---- MODE A: NEW PROJECT FLOW ----
        render_header()
        
        idea = st.text_area(
            "Product Idea",
            placeholder="What are we building today?\n\nExample: Build an AI healthcare platform that helps doctors monitor diabetic patients through wearable devices and personalized recommendations.",
            height=130,
            label_visibility="collapsed"
        )
        
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
                deliverable = st.selectbox(
                    "Target Deliverable",
                    options=[
                        "Product Requirements Document (PRD)",
                        "Business Requirements Document (BRD)",
                        "Software Requirements Specification (SRS)",
                        "Technical Design Document (TDD)",
                        "User Stories",
                        "Sprint Backlog",
                        "Jira Tasks",
                        "Executive Summary",
                        "Product Roadmap"
                    ]
                )
            with col5:
                st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
                include_risk = st.checkbox("Include Risk Analysis", value=True)
                
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        
        col_left, col_mid, col_right = st.columns([1.5, 2, 1.5])
        with col_mid:
            if st.button("Create Blueprint →", type="primary"):
                if idea.strip():
                    simulate_new_project_generation(idea, industry, product_type, audience, deliverable, include_risk)
                    st.rerun()
                else:
                    st.warning("Please describe your product idea first.")
                    
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # New Project Mode Empty State
        st.markdown("""
            <div class="empty-state">
                <span class="empty-icon">🧊</span>
                <h3>Start with an idea.</h3>
                <p>ProductPilot will help transform it into structured product documentation that evolves with your project.</p>
            </div>
        """, unsafe_allow_html=True)
        
    else:
        # ---- MODE B: PERSISTENT ACTIVE PROJECT WORKSPACE ----
        project = st.session_state['projects'][active_id]
        
        # Render a header styled like a persistent workspace directory
        st.markdown(f"""
            <div style='margin-bottom: 2rem;'>
                <div style='font-size: 0.85rem; color: #4F8CFF; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;'>Active Workspace</div>
                <h1 style='font-size: 2.5rem; font-weight: 800; color: #F5F5F5; margin-top: 0.25rem; letter-spacing: -0.03em;'>📁 {project['name']}</h1>
                <p style='color: #9E9E9E; font-size: 0.95rem; margin-top: 0.5rem;'>{project['idea']}</p>
                <div style='font-size: 0.8rem; color: #6B7280; margin-top: 0.5rem;'>
                    <strong>Industry:</strong> {project['industry']} | 
                    <strong>Product Type:</strong> {project['product_type']} | 
                    <strong>Audience:</strong> {project['audience']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Tabs corresponding to potential artifact deliverables
        tab_names = [
            "PRD", 
            "BRD", 
            "SRS", 
            "User Stories", 
            "Roadmap", 
            "Jira Tasks", 
            "Sprint Backlog"
        ]
        tabs = st.tabs(tab_names)
        
        # Handle Tab Generation Requests
        generating_tab = st.session_state.get('generating_tab', None)
        if generating_tab:
            progress_container = st.empty()
            with progress_container.container():
                render_progress_panel(step=2, deliverable_name=generating_tab)
            time.sleep(1.8)
            
            # Populate content mock data for that tab
            mock_tabs_data = {
                "Product Requirements Document (PRD)": {
                    "🎯 Problem Statement": "System lacks continuous telemetry logging frameworks.",
                    "✨ Key Features": "Continuous Glucose Monitor passive sync routines."
                },
                "Business Requirements Document (BRD)": {
                    "📈 Market Overview": "High potential for passive tracking inside medical sectors.",
                    "💰 Financial Model": "SaaS per-seat billing to medical clinic accounts."
                },
                "Software Requirements Specification (SRS)": {
                    "⚙️ API Schema": "GET /api/v1/telemetry/glucose\nPOST /api/v1/alert/dispatch",
                    "🔒 Compliance": "HIPAA encrypted storage protocols using AES-256."
                },
                "User Stories": {
                    "📖 Doctor View": "- *As a practitioner, I want to review hourly trend statistics to assess medication effectiveness.*"
                },
                "Product Roadmap": {
                    "🗓️ Milestone 1": "Setup continuous API ingest pipeline (ETA: Month 2)."
                },
                "Jira Tasks": {
                    "🎫 PM-101": "Write validation logic for incoming blood glucose readings.\n- Priority: High\n- Estimate: 3 Story Points"
                },
                "Sprint Backlog": {
                    "🏃 Sprint 1 Goals": "- Configure database schemas.\n- Integrate authentication keys."
                }
            }
            
            project['deliverables'][generating_tab] = {
                "content": mock_tabs_data.get(generating_tab, {"Output": "Compiled details draft."})
            }
            st.session_state['generating_tab'] = None
            progress_container.empty()
            st.rerun()

        for idx, tab_name in enumerate(tab_names):
            with tabs[idx]:
                # Map shorthand tab name to full deliverable dictionary key
                map_name = tab_name
                if tab_name == "PRD":
                    map_name = "Product Requirements Document (PRD)"
                elif tab_name == "BRD":
                    map_name = "Business Requirements Document (BRD)"
                elif tab_name == "SRS":
                    map_name = "Software Requirements Specification (SRS)"
                elif tab_name == "Roadmap":
                    map_name = "Product Roadmap"
                
                # Check if this deliverable has content compiled
                if map_name in project['deliverables']:
                    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                    doc_data = project['deliverables'][map_name]["content"]
                    for section_title, section_content in doc_data.items():
                        st.markdown(f"""
                            <div class="prd-section">
                                <div class="prd-section-title">{section_title}</div>
                                <div class="prd-section-content">{section_content.replace(chr(10), '<br>')}</div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    # Noncompiled State UI
                    st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style='text-align: center; color: #9E9E9E; padding: 4rem 2rem; border: 1px dashed #2A2A2A; border-radius: 10px;'>
                            <span style='font-size: 2rem; display: block; margin-bottom: 0.5rem;'>📄</span>
                            <h4 style='color: #F5F5F5; font-weight: 500; margin-bottom: 0.25rem;'>{tab_name} is not compiled yet</h4>
                            <p style='font-size: 0.9rem;'>Establish and build out this deliverable for {project['name']}.</p>
                        </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                    
                    # Generate Button for this specific Deliverable
                    col_l, col_m, col_r = st.columns([1.5, 2, 1.5])
                    with col_m:
                        if st.button(f"Generate {tab_name} →", key=f"gen_{tab_name}_{project['name']}", type="primary"):
                            st.session_state['generating_tab'] = map_name
                            st.rerun()

if __name__ == "__main__":
    main()
