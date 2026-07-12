import streamlit as st
from typing import Tuple, Dict, Any
from ui.forms import render_project_configuration
from ui.output import render_project_deliverables
from backend.api import create_project

def render_hero() -> None:
    """Renders the top branding header with updated visual hierarchy."""
    st.markdown("""
        <div style="text-align: center; margin-top: 1.5rem; margin-bottom: 2.5rem;">
            <div class="hero-badge">AI Product Management Workspace</div>
            <h1 class="logo-title">ProductPilot</h1>
            <p class="tagline">Transform rough ideas into production-ready product documentation.</p>
        </div>
    """, unsafe_allow_html=True)

def render_idea_input() -> str:
    """Renders the product idea input writing canvas and suggestion chips."""
    idea = st.text_area(
        "Describe your product idea",
        value=st.session_state['idea_input'],
        placeholder="Example:\nBuild a healthcare platform where patients can consult doctors online, manage prescriptions, schedule appointments, and receive AI-powered health recommendations.",
        height=130
    )
    
    char_count = len(idea)
    st.markdown(f"<div style='text-align: right; color: #6B7280; font-size: 0.8rem; margin-top: -0.65rem; margin-bottom: 1.25rem;'>{char_count} characters</div>", unsafe_allow_html=True)
    
    # Suggestion Chips / Example Projects
    st.markdown("<div style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 0.25rem;'>Example Projects:</div>", unsafe_allow_html=True)
    
    chip_cols = st.columns(6)
    chips = ["Healthcare AI", "Food Delivery", "AI Tutor", "Inventory Sync", "CRM SaaS", "Smart Farm"]
    prompts = {
        "Healthcare AI": "Build a healthcare platform where patients can consult doctors online, manage prescriptions, schedule appointments, and receive AI-powered health recommendations.",
        "Food Delivery": "A hyper-local food delivery marketplace optimized for eco-friendly drone shipping and zero-waste packaging.",
        "AI Tutor": "An AI-powered tutoring application that adaptively teaches high school mathematics through interactive storytelling.",
        "Inventory Sync": "An automated inventory management suite for warehouses utilizing real-time sensor streams and automated supply reordering.",
        "CRM SaaS": "A privacy-first CRM SaaS designed for security-conscious enterprise teams with local-first syncing and end-to-end encryption.",
        "Smart Farm": "An IoT-enabled smart agriculture workspace that monitors soil quality, schedules automated irrigation, and predicts harvest cycles."
    }
    
    for idx, chip_name in enumerate(chips):
        with chip_cols[idx]:
            st.markdown("<div class='chip-col'>", unsafe_allow_html=True)
            if st.button(chip_name, key=f"chip_{chip_name}"):
                st.session_state['idea_input'] = prompts[chip_name]
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    return idea

def render_generate_button(idea: str, config: Tuple[str, str, str, str, str, bool]) -> None:
    """Renders the centered Create Blueprint CTA button and handles generation logic."""
    industry, product_type, audience, deliverable, detail_level, include_risk = config
    col_left, col_mid, col_right = st.columns([1.2, 2.6, 1.2])
    with col_mid:
        if st.button("Create Blueprint →", type="primary", use_container_width=True):
            if idea.strip():
               payload = {
                    "project": {
                        "idea": idea,
                        "industry": industry,
                        "product_type": product_type,
                        "audience": audience,
                        "deliverable": deliverable,
                        "detail_level": detail_level,
                        "risk_analysis": include_risk
                    }
                }

            result = create_project(payload)
               # TEMPORARY (for testing)
            st.json(result)
               
            if response["success"]:
                    st.success("Connected!")
                    st.json(response["data"])
            else:
                    st.error(f"Backend connection failed: {response.get('error')}")
        else:
         st.warning("Please describe your product idea first.")

def render_empty_state() -> None:
    """Renders empty state message for new project templates."""
    st.markdown("""
        <div class="empty-state">
            <span class="empty-icon">🧊</span>
            <h3>Start with an idea.</h3>
            <p>ProductPilot will help transform it into structured product documentation that evolves with your project.</p>
        </div>
    """, unsafe_allow_html=True)

def render_project_header(project: Dict[str, Any]) -> None:
    """Renders active workspace details header directory."""
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

def render_home() -> None:
    """Orchestrates page layout checks and triggers core rendering flows."""
    active_id = st.session_state.get('active_project_id', None)
    
    if active_id is None:
        # Mode A: New Project Flow
        render_hero()
        idea = render_idea_input()
        config = render_project_configuration()
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        render_generate_button(idea, config)
        st.markdown("<hr>", unsafe_allow_html=True)
        render_empty_state()
    else:
        # Mode B: Persistent Active Project Workspace
        project = st.session_state['projects'][active_id]
        render_project_header(project)
        render_project_deliverables(project)
