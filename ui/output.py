import streamlit as st
import time
from typing import Dict, Any
from backend.agents.workspace_editor import update_workspace

def render_progress_panel(step: int, deliverable_name: str = "Product Requirements Document (PRD)") -> None:
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

def render_project_deliverables(project: Dict[str, Any]) -> None:
    """Renders the document deliverables inside tabs for an active project."""
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

    # --- AI Workspace Editor Section ---
    st.markdown("<hr style='border-top: 1px solid #2A2A2A; margin: 3rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>⚡ AI Workspace Editor</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1.25rem;'>Provide refinement instructions to edit features, personas, or roadmap phases globally across the workspace.</p>", unsafe_allow_html=True)
    
    edit_instruction = st.text_area(
        "Refinement Instructions",
        placeholder="Example:\nAdd a feature for push notifications for scheduled doctor visits, and ensure it is prioritized as High in Phase 1.",
        key=f"edit_inst_{project['name']}",
        height=100
    )
    
    if st.button("Apply Changes", type="primary", key=f"apply_{project['name']}"):
        if edit_instruction.strip():
            with st.spinner("AI Workspace Editor applying updates..."):
                try:
                    updated_project = update_workspace(project, edit_instruction)
                    st.session_state['projects'][project['name']] = updated_project
                    st.success("Workspace updated successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to apply changes: {e}")
        else:
            st.warning("Please provide a refinement instruction first.")
