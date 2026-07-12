import streamlit as st
import time
from typing import Dict, Any

def render_progress_panel(step: int, deliverable_name: str) -> None:
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

def get_full_name(tab_name: str) -> str:
    """Maps short tab shorthand string names to full deliverables dictionary keys."""
    if tab_name == "PRD":
        return "Product Requirements Document (PRD)"
    elif tab_name == "BRD":
        return "Business Requirements Document (BRD)"
    elif tab_name == "SRS":
        return "Software Requirements Specification (SRS)"
    elif tab_name == "Roadmap":
        return "Product Roadmap"
    else:
        return tab_name

def run_lazy_agent(tab_name: str, project: Dict[str, Any]) -> Dict[str, Any]:
    """Invokes the specific specialized AI Agent based on target tab selection."""
    if tab_name == "BRD":
        from backend.agents.brd_agent import generate_brd
        return generate_brd(project)
    elif tab_name == "SRS":
        from backend.agents.srs_agent import generate_srs
        return generate_srs(project)
    elif tab_name == "User Stories":
        from backend.agents.user_story_agent import generate_user_stories
        return generate_user_stories(project)
    elif tab_name == "Roadmap":
        from backend.agents.roadmap_agent import generate_roadmap
        return generate_roadmap(project)
    elif tab_name == "Jira Tasks":
        from backend.agents.jira_agent import generate_jira_tasks
        return generate_jira_tasks(project)
    elif tab_name == "Sprint Backlog":
        from backend.agents.sprint_planning_agent import generate_sprint_backlog
        return generate_sprint_backlog(project)
    else:
        raise ValueError(f"Unknown lazy agent domain tab: {tab_name}")

def render_project_deliverables(project: Dict[str, Any]) -> None:
    """Renders document deliverables tabs dynamically showing compilation status."""
    tab_names = [
        "PRD", 
        "BRD", 
        "SRS", 
        "User Stories", 
        "Roadmap", 
        "Jira Tasks", 
        "Sprint Backlog"
    ]
    
    # 🟢 green circle indicator if generated, otherwise white text
    tab_titles = []
    for name in tab_names:
        full_name = get_full_name(name)
        if full_name in project.get('deliverables', {}):
            tab_titles.append(f"🟢 {name}")
        else:
            tab_titles.append(name)
            
    tabs = st.tabs(tab_titles)

    for idx, tab_name in enumerate(tab_names):
        with tabs[idx]:
            map_name = get_full_name(tab_name)
            
            # Check if this deliverable has content compiled
            if map_name in project.get('deliverables', {}):
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                doc_data = project['deliverables'][map_name]["content"]
                
                # Render document sections
                for section_title, section_content in doc_data.items():
                    st.markdown(f"""
                        <div class="prd-section">
                            <div class="prd-section-title">{section_title}</div>
                            <div class="prd-section-content">{section_content.replace(chr(10), '<br>')}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                # Targeted Refinement Section for this document page
                st.markdown("<hr style='border-top: 1px solid #2A2A2A; margin: 2rem 0;'>", unsafe_allow_html=True)
                st.markdown(f"<h4 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>⚡ Refine {tab_name}</h4>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1rem;'>Provide refinement instructions to edit sections of this {tab_name} document.</p>", unsafe_allow_html=True)
                
                refine_input = st.text_area(
                    f"Instruction for {tab_name}",
                    placeholder=f"Example:\nAdd details to clarify data integration parameters or user workflows...",
                    key=f"refine_in_{tab_name}_{project['name']}",
                    height=80,
                    label_visibility="collapsed"
                )
                
                # Determine button label based on specs
                button_label = f"Refine {tab_name}"
                if tab_name == "Roadmap":
                    button_label = "Expand Roadmap"
                elif tab_name == "Jira Tasks":
                    button_label = "Generate Additional Tasks"
                    
                if st.button(button_label, key=f"refine_btn_{tab_name}_{project['name']}", type="primary"):
                    if refine_input.strip():
                        with st.spinner(f"Refining {tab_name}..."):
                            try:
                                from backend.agents.document_refiner import refine_document
                                current_content = project['deliverables'][map_name]["content"]
                                
                                # Call document specific refiner
                                updated_content = refine_document(
                                    document_name=map_name,
                                    current_content=current_content,
                                    instruction=refine_input,
                                    workspace=project
                                )
                                
                                # Cache updated deliverables content
                                project['deliverables'][map_name]["content"] = updated_content
                                st.success(f"{tab_name} refined successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to refine {tab_name}: {e}")
                    else:
                        st.warning("Please provide a refinement instruction.")
            else:
                # Noncompiled State UI
                st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style='text-align: center; color: #9E9E9E; padding: 4rem 2rem; border: 1px dashed #2A2A2A; border-radius: 10px;'>
                        <span style='font-size: 2rem; display: block; margin-bottom: 0.5rem;'>📄</span>
                        <h4 style='color: #F5F5F5; font-weight: 500; margin-bottom: 0.25rem;'>This document has not been generated yet.</h4>
                        <p style='font-size: 0.9rem;'>This document will be generated on demand.</p>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                
                # Placeholder button — no agent invocation
                col_l, col_m, col_r = st.columns([1.5, 2, 1.5])
                with col_m:
                    if st.button(f"✨ Generate {tab_name}", key=f"lazy_gen_{tab_name}_{project['name']}", type="primary", use_container_width=True):
                        st.info("Generation coming in the next step.")

