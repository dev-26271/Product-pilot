import streamlit as st
import time
from typing import Dict, Any
from backend.agents.workspace_chat import chat_refine_workspace

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

    # --- AI Product Manager Chat Panel ---
    st.markdown("<hr style='border-top: 1px solid #2A2A2A; margin: 3rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>💬 AI Product Manager Refinement Chat</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1.25rem;'>Work iteratively with a senior PM to refine features, personas, or adjust roadmap releases across your workspace deliverables.</p>", unsafe_allow_html=True)
    
    # Initialize chat history inside project if not present
    if 'chat_history' not in project:
        project['chat_history'] = [
            {
                "role": "assistant", 
                "content": f"Hello, I am your senior Product Manager. How can I help refine **{project['name']}** today?"
            }
        ]
        
    # Render scrollable Chat Container
    chat_container = st.container(height=300, border=True)
    with chat_container:
        for msg in project['chat_history']:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])
                
    # Multiline chat input
    user_chat_input = st.text_area(
        "Refine strategy / Ask a question",
        placeholder="Type your instruction or question...",
        key=f"chat_in_{project['name']}",
        height=80,
        label_visibility="collapsed"
    )
    
    # Send Button
    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("Send", type="primary", use_container_width=True, key=f"send_{project['name']}"):
            if user_chat_input.strip():
                # Save user message to history
                project['chat_history'].append({"role": "user", "content": user_chat_input})
                
                with st.spinner("AI Product Manager analyzing..."):
                    try:
                        # Run PM refinement logic passing current history (excluding new message to act as history context)
                        chat_result = chat_refine_workspace(
                            workspace=project,
                            chat_history=project['chat_history'][:-1],
                            user_message=user_chat_input
                        )
                        
                        # Save response to history
                        project['chat_history'].append({
                            "role": "assistant", 
                            "content": chat_result["chat_response"]
                        })
                        
                        # If deliverables were updated, replace them
                        if chat_result.get("updated_tabs"):
                            project['deliverables'] = chat_result["deliverables"]
                            st.toast(f"Updated sections: {', '.join(chat_result['updated_tabs'])}")
                            
                        st.success("Refined successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error executing refinement: {e}")
            else:
                st.warning("Please enter a message first.")
