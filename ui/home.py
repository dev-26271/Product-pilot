import streamlit as st
from typing import Tuple, Dict, Any
from ui.forms import render_project_configuration, render_execution_mode
from ui.output import render_project_deliverables, render_chat_refinement, render_knowledge_sources
from backend.orchestrator import generate_prd, infer_project_metadata

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
        placeholder="Examples:\n- An AI tutoring platform that adapts to each student's learning style\n- A hyper-local food delivery marketplace with eco-friendly drone shipping\n- An automated inventory management system with real-time sensor tracking\n- A personal finance assistant that automates budgeting and investing\n- A smart farming platform that monitors soil and predicts harvest cycles",
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

def render_generate_button(idea: str, config: Tuple[str, str, str, str, str, bool], execution_mode: str) -> None:
    """Renders the centered Create Blueprint CTA button and handles generation logic."""
    industry, product_type, audience, deliverable, detail_level, include_risk = config
    col_left, col_mid, col_right = st.columns([1.2, 2.6, 1.2])
    with col_mid:
        if st.button("Create Blueprint →", type="primary", use_container_width=True):
            if idea.strip():
                # ── Resolve Auto Detect fields via lightweight classifier ──
                resolved_industry = industry
                resolved_product_type = product_type
                resolved_audience = audience
                
                needs_inference = (
                    industry == "Auto Detect" or
                    product_type == "Auto Detect" or
                    audience == "Auto Detect"
                )
                
                if needs_inference:
                    with st.spinner("Detecting project metadata from your idea..."):
                        inferred = infer_project_metadata(idea)
                    if industry == "Auto Detect":
                        resolved_industry = inferred.get("industry", "Other")
                    if product_type == "Auto Detect":
                        resolved_product_type = inferred.get("product_type", "SaaS Platform")
                    if audience == "Auto Detect":
                        resolved_audience = inferred.get("audience", "B2C")
                
                payload = {
                    "project": {
                        "idea": idea,
                        "industry": resolved_industry,
                        "product_type": resolved_product_type,
                        "audience": resolved_audience,
                        "deliverable": deliverable,
                        "detail_level": detail_level,
                        "risk_analysis": include_risk
                    },
                    "mode": execution_mode
                }
                
                with st.spinner("ProductPilot generating PRD & Auditing Alignment..."):
                    result = generate_prd(payload)
                
                if result.get("success"):
                    # Derive a clean project name
                    proj_name = " ".join(idea.split()[:2]) + " Project"
                    
                    # Reset projects dict and active ID
                    st.session_state['projects'] = {}
                    st.session_state['active_project_id'] = None
                    
                    # Store context dictionary in session state directly
                    st.session_state['projects'][proj_name] = {
                        "name": proj_name,
                        "metadata": "Active",
                        "idea": idea,
                        "industry": resolved_industry,
                        "product_type": resolved_product_type,
                        "audience": resolved_audience,
                        "intent_context": result.get("intent_context", {}),
                        "business_analysis": result.get("business_analysis", {}),
                        "prd": result.get("prd", {}),
                        "deliverables": result["data"],
                        "agent_logs": result.get("agent_logs", []),
                        "metadata_context": result.get("metadata", {}),
                        "rag_context": result.get("rag_context", [])
                    }
                    st.session_state['active_project_id'] = proj_name
                    st.success("Validated PRD generated — workspace ready!")
                    st.rerun()
                else:
                    st.error(f"Orchestration failed: {result.get('error')}")
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
    """Renders active workspace details header with confidence scores and validation badges."""
    meta = project.get("metadata_context", {})
    ind_conf = meta.get("industry_confidence")
    pt_conf = meta.get("product_type_confidence")
    aud_conf = meta.get("audience_confidence")
    
    # Validation status
    val_report = meta.get("validation_report", {})
    if val_report:
        score = val_report.get("score", 1.0)
        is_valid = val_report.get("valid", True)
        if is_valid:
            val_badge = f"<span style='color: #22C55E; font-weight: 600; margin-left: 10px;'>✓ Validated (Score: {score*100:.0f}%)</span>"
        else:
            val_badge = f"<span style='color: #EF4444; font-weight: 600; margin-left: 10px;'>⚠ Validation failed (Score: {score*100:.0f}%)</span>"
    else:
        val_badge = ""

    ind_str = f"{project['industry']} ({(ind_conf*100):.0f}% conf)" if ind_conf is not None else project['industry']
    pt_str = f"{project['product_type']} ({(pt_conf*100):.0f}% conf)" if pt_conf is not None else project['product_type']
    aud_str = f"{project['audience']} ({(aud_conf*100):.0f}% conf)" if aud_conf is not None else project['audience']

    st.markdown(f"""
        <div style='margin-bottom: 2rem;'>
            <div style='font-size: 0.85rem; color: #4F8CFF; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;'>Active Workspace</div>
            <h1 style='font-size: 2.5rem; font-weight: 800; color: #F5F5F5; margin-top: 0.25rem; letter-spacing: -0.03em; display: inline-block;'>📁 {project['name']}</h1>
            {val_badge}
            <p style='color: #9E9E9E; font-size: 0.95rem; margin-top: 0.5rem;'>{project['idea']}</p>
            <div style='font-size: 0.8rem; color: #6B7280; margin-top: 0.5rem;'>
                <strong>Industry:</strong> {ind_str} | 
                <strong>Product Type:</strong> {pt_str} | 
                <strong>Audience:</strong> {aud_str}
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
        execution_mode = render_execution_mode()
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        render_generate_button(idea, config, execution_mode)
        st.markdown("<hr>", unsafe_allow_html=True)
        render_empty_state()
    else:
        # Mode B: Persistent Active Project Workspace
        project = st.session_state['projects'][active_id]
        if "metadata" not in project or not isinstance(project["metadata"], dict):
            last_updated = project.get("metadata") if isinstance(project.get("metadata"), str) else "Updated just now"
            project["metadata"] = {
                "last_updated": last_updated,
                "chat_history": [],
                "version_history": []
            }
        render_project_header(project)
        render_knowledge_sources(project)
        render_project_deliverables(project)
        render_chat_refinement(project)
