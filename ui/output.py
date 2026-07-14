import streamlit as st
import time
from typing import Dict, Any

# Import modular components from subfolders to maintain clean architecture
from ui.components.common import render_progress_panel, get_full_name, run_lazy_agent, _badge
from ui.components.user_stories import render_user_stories
from ui.components.prd import render_prd_entities
from ui.components.roadmap import render_roadmap_entities
from ui.components.jira import render_jira_entities
from ui.components.export import render_export_center
from ui.components.chat import render_chat_refinement
from ui.components.knowledge import render_knowledge_sources, render_rag_inspector
from ui.components.dashboard import render_workspace_dashboard
from ui.components.traceability import render_traceability_explorer

def render_project_deliverables(project: Dict[str, Any]) -> None:
    """Renders document deliverables tabs dynamically showing compilation status.
    
    Delegates component layouts to modular components.
    """
    tab_names = [
        "PRD", 
        "BRD", 
        "SRS", 
        "User Stories", 
        "Roadmap", 
        "Jira Tasks", 
        "Sprint Backlog",
        "Export Center"
    ]
    
    # 🟢 green circle indicator if generated, otherwise white text
    tab_titles = []
    for name in tab_names:
        if name == "Export Center":
            tab_titles.append("📤 Export Center")
            continue
        full_name = get_full_name(name)
        if full_name in project.get('deliverables', {}):
            tab_titles.append(f"🟢 {name}")
        else:
            tab_titles.append(name)
            
    tabs = st.tabs(tab_titles)

    for idx, tab_name in enumerate(tab_names):
        with tabs[idx]:
            if tab_name == "Export Center":
                render_export_center(project)
                continue
                
            map_name = get_full_name(tab_name)
            
            # Check if this deliverable has content compiled
            if map_name in project.get('deliverables', {}):
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                doc_data = project['deliverables'][map_name]

                # Delegate rendering based on tab
                if tab_name == "User Stories":
                    us_data = doc_data.get("content", doc_data)
                    render_user_stories(us_data)

                elif tab_name == "PRD" and (doc_data.get("entities") or project.get("prd")):
                    render_prd_entities(project.get("prd") or doc_data.get("entities"))

                elif tab_name == "Roadmap" and doc_data.get("entities", {}).get("phases"):
                    render_roadmap_entities(doc_data["entities"]["phases"])

                elif tab_name == "Jira Tasks" and doc_data.get("entities", {}).get("tasks"):
                    render_jira_entities(doc_data["entities"]["tasks"])

                else:
                    # All other documents: generic section-by-section renderer
                    content = doc_data.get("content", doc_data)
                    for section_title, section_content in content.items():
                        st.markdown(f"""
                            <div class="prd-section">
                                <div class="prd-section-title">{section_title}</div>
                                <div class="prd-section-content">{str(section_content).replace(chr(10), '<br>')}</div>
                            </div>
                        """, unsafe_allow_html=True)

                # Targeted Refinement Section — not shown for User Stories
                if tab_name != "User Stories":
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
                                    current_content = project['deliverables'][map_name].get("content", project['deliverables'][map_name])

                                    # Call document specific refiner
                                    updated_content = refine_document(
                                        document_name=map_name,
                                        current_content=current_content,
                                        instruction=refine_input,
                                        workspace=project
                                    )
                                    
                                    # Cache updated deliverables content
                                    project['deliverables'][map_name]["content"] = updated_content
                                    from backend.version_history import VersionControl
                                    project = VersionControl.create_version(
                                        project,
                                        action=f"Refine {tab_name}",
                                        summary=f"Refined deliverables: {refine_input}",
                                        author="User"
                                    )
                                    active_id = st.session_state.get('active_project_id')
                                    st.session_state['projects'][active_id] = project
                                    st.success(f"{tab_name} refined successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to refine {tab_name}: {e}")
                        else:
                            st.warning("Please provide a refinement instruction.")
            else:
                # Noncompiled State UI — shown when tab is opened but document not yet generated
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class='empty-state' style='padding: 3rem 2rem; border: 1px dashed #222222; border-radius: 10px;'>
                        <span class='empty-icon'>○</span>
                        <h3>{tab_name} not generated</h3>
                        <p>Click below to compile this document using the AI pipeline.</p>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                
                # Generate button
                col_l, col_m, col_r = st.columns([1.5, 2, 1.5])
                with col_m:
                    if st.button("Generate", key=f"lazy_gen_{tab_name}_{project['name']}", type="primary", use_container_width=True):
                        with st.spinner(f"Generating {tab_name}..."):
                            try:
                                from backend.profiler import PerformanceProfiler
                                profiler = PerformanceProfiler.get_instance()
                                profiler.reset()
                                profiler.start(tab_name)
                                profiler.start("TOTAL")
                                generated_content = run_lazy_agent(tab_name, project)
                                profiler.end(tab_name)
                                profiler.end("TOTAL")
                                
                                # Store timings inside context dict
                                if "performance" not in project:
                                    project["performance"] = {}
                                project["performance"][tab_name] = profiler.get_duration(tab_name)
                                project["performance"]["TOTAL"] = profiler.get_duration("TOTAL")
                                
                                # Print clean summary timing report
                                print(profiler.summary())
                                
                                # User Stories returns raw structured JSON — store directly.
                                if tab_name == "User Stories":
                                    project['deliverables'][map_name] = generated_content
                                else:
                                    project['deliverables'][map_name] = {
                                        "content": generated_content
                                    }
                                
                                # Log version update
                                from backend.version_history import VersionControl
                                project = VersionControl.create_version(
                                    project,
                                    action=f"Generate {tab_name}",
                                    summary=f"Successfully generated {tab_name} deliverables via lazy compilation.",
                                    author="ProductPilot"
                                )
                                active_id = st.session_state.get('active_project_id')
                                st.session_state['projects'][active_id] = project
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to generate {tab_name}: {e}")
