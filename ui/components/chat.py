import streamlit as st
import time
from datetime import datetime
from typing import Dict, Any, List
from backend.formatters import format_inr_text
from ui.components.version_history import render_version_history

def render_chat_header() -> None:
    """Renders the styled header section for the chat copilot."""
    st.markdown("<hr style='border-top: 1px solid #2A2A2A; margin: 3rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>💬 Ask ProductPilot</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1.5rem;'>Collaborate with a Senior Product Manager to understand, critique, explain, and incrementally modify your workspace deliverables. Ask questions, analyze tradeoffs, or request changes.</p>", unsafe_allow_html=True)

def render_chat_history(chat_history: List[Dict[str, Any]]) -> None:
    """Renders past chat messages and their reasoning traces."""
    for msg in chat_history:
        role = msg["role"]
        content = msg["content"]
        with st.chat_message(role):
            display_content = format_inr_text(content) if role == "assistant" else content
            st.markdown(display_content)
            
            # Reasoning Trace expander
            trace = msg.get("reasoning_trace")
            if trace and role == "assistant":
                with st.expander("🔍 Reasoning Trace", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem; color: #E5E7EB;'>Sources Consulted</p>", unsafe_allow_html=True)
                        sources = trace.get("sources_consulted", [])
                        if isinstance(sources, str):
                            sources = [sources]
                        for s in ["Business Analysis", "Product Requirements Document", "PRD", "User Stories", "Roadmap", "Jira Tasks", "Validation Report", "Intent Context"]:
                            if s in sources or (s == "PRD" and "Product Requirements Document" in sources) or (s == "Product Requirements Document" and "PRD" in sources):
                                st.markdown(f"<span style='font-size: 0.82rem; color: #22C55E;'>✓ {s}</span>", unsafe_allow_html=True)
                                
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; margin-top: 0.75rem; margin-bottom: 0.25rem; color: #E5E7EB;'>Validation</p>", unsafe_allow_html=True)
                        checks = trace.get("validation_checks", [])
                        if isinstance(checks, str):
                            checks = [checks]
                        if checks:
                            for check in checks:
                                st.markdown(f"<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'>- {check}</p>", unsafe_allow_html=True)
                        else:
                            st.markdown("<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'>No validation anomalies detected.</p>", unsafe_allow_html=True)
                            
                    with col2:
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem; color: #E5E7EB;'>Entities Referenced</p>", unsafe_allow_html=True)
                        entities = trace.get("entities_referenced", [])
                        if isinstance(entities, str):
                            entities = [entities]
                        if entities:
                            st.markdown(" ".join([f"`{e}`" for e in entities]))
                        else:
                            st.markdown("<span style='font-size: 0.82rem; color: #9CA3AF;'>None</span>", unsafe_allow_html=True)
                            
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; margin-top: 0.75rem; margin-bottom: 0.25rem; color: #E5E7EB;'>Traceability Chain</p>", unsafe_allow_html=True)
                        chain = trace.get("traceability_chain", [])
                        if isinstance(chain, str):
                            chain = [chain]
                        if chain:
                            for c in chain:
                                st.markdown(f"`{c}`")
                        else:
                            st.markdown("<span style='font-size: 0.82rem; color: #9CA3AF;'>None</span>", unsafe_allow_html=True)
                        
                        # Confidence display
                        conf = trace.get("confidence", 0.95)
                        if isinstance(conf, str):
                            conf_val = conf
                        else:
                            if conf <= 1.0:
                                conf_val = f"{int(conf * 100)}%"
                            else:
                                conf_val = f"{int(conf)}%"
                        st.markdown(f"<p style='font-size: 0.85rem; font-weight: 600; margin-top: 0.75rem; color: #E5E7EB;'>Confidence: <span style='color:#3B82F6;'>{conf_val}</span></p>", unsafe_allow_html=True)
                        
                    # Optional fields for modifications
                    has_mod_fields = any(trace.get(k) for k in ["affected_documents", "affected_entities", "estimated_changes", "validation_required", "recommended_action"])
                    if has_mod_fields:
                        st.markdown("<hr style='border-top: 1px solid #2D2D2D; margin: 0.75rem 0;'>", unsafe_allow_html=True)
                        st.markdown("<p style='font-size: 0.85rem; font-weight: 600; color: #E5E7EB; margin-bottom: 0.5rem;'>📋 Modification Workspace Analysis</p>", unsafe_allow_html=True)
                        
                        col3, col4 = st.columns(2)
                        with col3:
                            docs = trace.get("affected_documents")
                            if docs:
                                if isinstance(docs, str):
                                    docs = [docs]
                                st.markdown(f"<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'><strong>Affected Documents:</strong> {', '.join(docs)}</p>", unsafe_allow_html=True)
                                
                            ents = trace.get("affected_entities")
                            if ents:
                                if isinstance(ents, str):
                                    ents = [ents]
                                st.markdown(f"<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'><strong>Affected Entities:</strong> {', '.join([f'`{e}`' for e in ents])}</p>", unsafe_allow_html=True)
                                
                            est = trace.get("estimated_changes")
                            if est:
                                st.markdown(f"<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'><strong>Estimated Changes:</strong> {est}</p>", unsafe_allow_html=True)
                                
                        with col4:
                            v_req = trace.get("validation_required")
                            if v_req:
                                st.markdown(f"<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'><strong>Validation Required:</strong> {v_req}</p>", unsafe_allow_html=True)
                                
                            rec = trace.get("recommended_action")
                            if rec:
                                st.markdown(f"<p style='font-size: 0.82rem; color: #9CA3AF; margin: 0;'><strong>Recommended Action:</strong> {rec}</p>", unsafe_allow_html=True)

def render_pending_impact(project: Dict[str, Any], pending_impact: Dict[str, Any]) -> None:
    """Renders Workspace Change Impact Analysis layout and approval buttons."""
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    severity = pending_impact.get("severity", "Medium")
    severity_color = "#FF3B3B" if severity == "High" else "#FF8C00" if severity == "Medium" else "#22C55E"
    
    st.markdown(f"""
        <div style='background-color: #111827; border: 1px solid #2D2D2D; border-left: 4px solid {severity_color}; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;'>
            <h4 style='color: #F5F5F5; margin: 0 0 0.5rem 0; font-weight: 700; display:flex; justify-content:space-between; align-items:center;'>
                <span>🔍 Workspace Change Impact Analysis</span>
                <span style='color: {severity_color}; background-color: {severity_color}22; font-size: 0.8rem; padding: 2px 10px; border-radius: 12px; border: 1px solid {severity_color}44; font-weight:600;'>{severity} Severity</span>
            </h4>
            <p style='color: #E5E7EB; font-size: 0.9rem; margin-bottom: 0.75rem; margin-top: 0.5rem;'><strong>Proposed Change:</strong> "{pending_impact['instruction']}"</p>
            <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 0.8rem; font-size: 0.82rem; color: #9CA3AF;'>
                <div><strong>AI Cost Estimate:</strong> ${pending_impact['estimated_regeneration_cost']['usd_cost']:.4f} ({pending_impact['estimated_regeneration_cost']['tokens']} tokens)</div>
                <div><strong>Regeneration Time:</strong> {pending_impact['estimated_regeneration_time']}</div>
                <div><strong>PM Confidence:</strong> {int(pending_impact['confidence'] * 100)}%</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    entities = pending_impact.get("affected_entities", [])
    type_counts = {}
    for ent in entities:
        t = ent.get("type", "Entity")
        type_counts[t] = type_counts.get(t, 0) + 1
        
    st.markdown("<p style='font-size: 0.9rem; color: #E5E7EB; font-weight: 600; margin-bottom: 0.5rem;'>This change affects:</p>", unsafe_allow_html=True)
    
    for t, count in type_counts.items():
        st.markdown(f"✓ **{count} {t}s**")
        
    doc_list = pending_impact.get("affected_documents", [])
    for doc in doc_list:
        st.markdown(f"✓ **{doc}**")
        
    st.markdown("<p style='font-size: 0.82rem; color: #EF4444; font-weight: 600; margin-top: 0.5rem;'>⚠️ No changes have been applied yet.</p>", unsafe_allow_html=True)
    
    breaking = pending_impact.get("breaking_changes", [])
    if breaking:
        st.markdown("<p style='font-size: 0.88rem; color: #FF3B3B; font-weight: 700; margin-top: 1rem;'>⚠️ Breaking Changes Detected:</p>", unsafe_allow_html=True)
        for b in breaking:
            st.markdown(f"- <span style='color:#FF3B3B; font-size: 0.85rem;'>{b}</span>", unsafe_allow_html=True)
            
    warnings = pending_impact.get("warnings", [])
    if warnings:
        st.markdown("<p style='font-size: 0.88rem; color: #FF8C00; font-weight: 700; margin-top: 0.75rem;'>⚠️ Warnings:</p>", unsafe_allow_html=True)
        for w in warnings:
            st.markdown(f"- <span style='color:#FF8C00; font-size: 0.85rem;'>{w}</span>", unsafe_allow_html=True)
            
    recs = pending_impact.get("recommendations", [])
    if recs:
        st.markdown("<p style='font-size: 0.88rem; color: #4F8CFF; font-weight: 700; margin-top: 0.75rem;'>💡 Recommendations:</p>", unsafe_allow_html=True)
        for r in recs:
            st.markdown(f"- <span style='color:#4F8CFF; font-size: 0.85rem;'>{r}</span>", unsafe_allow_html=True)
            
    st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
    
    col_apply, col_review, col_cancel = st.columns([2.5, 2.5, 2])
    active_id = st.session_state.get('active_project_id')
    
    with col_apply:
        if st.button("Apply Automatically", type="primary", key="apply_impact_btn", use_container_width=True):
            with st.spinner("Applying refinements across affected documents..."):
                try:
                    from backend.agents.workspace_chat import apply_workspace_refinements
                    updated_workspace = apply_workspace_refinements(
                        workspace_dict=project,
                        instruction=pending_impact["instruction"],
                        affected_flags=pending_impact["affected"]
                    )
                    st.session_state['projects'][active_id] = updated_workspace
                    st.success("Refinements applied successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to apply refinements: {e}")
                    
    with col_review:
        review_key = f"review_details_{active_id}"
        if st.button("Review Affected Items", type="secondary", key="review_impact_btn", use_container_width=True):
            st.session_state[review_key] = not st.session_state.get(review_key, False)
            st.rerun()
            
    with col_cancel:
        if st.button("Cancel", type="secondary", key="cancel_impact_btn", use_container_width=True):
            project["metadata"].pop("pending_impact", None)
            st.success("Refinement cancelled.")
            time.sleep(0.5)
            st.rerun()
            
    if st.session_state.get(f"review_details_{active_id}", False):
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        with st.expander("🔍 Affected Entities Detail", expanded=True):
            if entities:
                for ent in entities:
                    st.markdown(f"- **{ent['id']}** ({ent['type']}): {ent['name']}")
            else:
                st.markdown("*No specific entities are downstream-impacted. The entire parent document will be incrementally refined.*")
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

def render_pending_approval(project: Dict[str, Any], pending_approval: Dict[str, Any]) -> None:
    """Renders approval flow for destructive scope changes."""
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style='background-color: #1A1A1A; border: 1px solid #FF4B4B; border-left: 4px solid #FF4B4B; padding: 1.2rem; border-radius: 6px; margin-bottom: 1.5rem;'>
            <h5 style='color: #FF4B4B; margin: 0 0 0.5rem 0; font-weight: 700;'>🛡️ Human Approval Required (Destructive Scope Change)</h5>
            <p style='color: #E5E7EB; font-size: 0.9rem; margin-bottom: 0.75rem;'><strong>Proposed Change:</strong> "{pending_approval['instruction']}"</p>
            <p style='color: #9CA3AF; font-size: 0.82rem; margin-bottom: 0.75rem;'><strong>Impact:</strong> {pending_approval['impact']}</p>
            <p style='color: #9CA3AF; font-size: 0.82rem; margin-bottom: 0.5rem;'><strong>Estimated Regeneration Time:</strong> {pending_approval['regeneration_time']}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("##### Affected Documents:")
    for k, v in pending_approval["affected"].items():
        doc_label = k.replace("_", " ").title()
        if v:
            st.markdown(f"🔴 **{doc_label}** — Will be modified/regenerated")
        else:
            st.markdown(f"⚪ *{doc_label}* — Unaffected")
            
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.5, 4])
    with col1:
        if st.button("Approve", type="primary", key="approve_refinement_btn", use_container_width=True):
            with st.spinner("Applying and regenerating critical changes..."):
                try:
                    from backend.agents.workspace_chat import apply_workspace_refinements
                    updated_workspace = apply_workspace_refinements(
                        workspace_dict=project,
                        instruction=pending_approval["instruction"],
                        affected_flags=pending_approval["affected"]
                    )
                    active_id = st.session_state.get('active_project_id')
                    st.session_state['projects'][active_id] = updated_workspace
                    st.success("Scope updates approved and applied successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to apply approved updates: {e}")
    with col2:
        if st.button("Reject", type="secondary", key="reject_refinement_btn"):
            project["metadata"].pop("pending_approval", None)
            st.success("Proposed scope updates rejected.")
            time.sleep(1)
            st.rerun()
            
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

def render_pending_changes(project: Dict[str, Any], pending_changes: Dict[str, Any]) -> None:
    """Renders simple document refinement proposals check list."""
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style='background-color: #1E1E1E; border-left: 4px solid #FF8C00; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;'>
            <h5 style='color: #FF8C00; margin: 0 0 0.5rem 0; font-weight: 600;'>Proposed Refinements Detected</h5>
            <p style='color: #D1D5DB; font-size: 0.85rem; margin-bottom: 0.75rem;'>The PM Agent analyzed your request and detected the following document updates:</p>
        </div>
    """, unsafe_allow_html=True)
    
    for k, v in pending_changes["affected"].items():
        doc_label = k.replace("_", " ").title()
        if v:
            st.markdown(f"🟢 **{doc_label}** — Will be regenerated")
        else:
            st.markdown(f"⚪ *{doc_label}* — Unaffected (No change)")
            
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1.5, 4])
    with col1:
        if st.button("Confirm & Apply", type="primary", key="confirm_refinement_btn", use_container_width=True):
            with st.spinner("Applying refinements across workspace..."):
                try:
                    from backend.agents.workspace_chat import apply_workspace_refinements
                    updated_workspace = apply_workspace_refinements(
                        workspace_dict=project,
                        instruction=pending_changes["instruction"],
                        affected_flags=pending_changes["affected"]
                    )
                    active_id = st.session_state.get('active_project_id')
                    st.session_state['projects'][active_id] = updated_workspace
                    st.success("Refinements applied successfully!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to apply refinements: {e}")
    with col2:
        if st.button("Cancel Refinement", type="secondary", key="cancel_refinement_btn"):
            project["metadata"].pop("pending_changes", None)
            st.rerun()
            
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

def render_starter_prompts() -> None:
    """Renders starter prompts grid layout."""
    st.markdown("<p style='font-size: 0.85rem; color: #9CA3AF; margin-top: 1.5rem; margin-bottom: 0.5rem; font-weight: 500;'>💡 Starter Prompts:</p>", unsafe_allow_html=True)
    
    starters = [
        ("📋 Summarize this project", "Summarize this project"),
        ("🔍 Review this PRD", "Review this PRD"),
        ("⚠️ Find missing requirements", "Find missing requirements"),
        ("🗓️ Explain this roadmap", "Explain this roadmap"),
        ("🎯 Suggest MVP scope", "Suggest MVP scope"),
        ("🛡️ Analyze project risks", "Analyze project risks"),
        ("💡 Recommend improvements", "Recommend improvements")
    ]
    
    col1, col2 = st.columns(2)
    for idx, (label, val) in enumerate(starters):
        with (col1 if idx % 2 == 0 else col2):
            if st.button(label, key=f"starter_prompt_{idx}", use_container_width=True):
                st.session_state["selected_starter"] = val
                st.rerun()
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

def render_chat_refinement(project: Dict[str, Any]) -> None:
    """Root entry point orchestrating the Ask ProductPilot chat sections."""
    render_chat_header()

    # Initialize metadata
    if "metadata" not in project or not isinstance(project["metadata"], dict):
        last_updated = project.get("metadata") if isinstance(project.get("metadata"), str) else "Updated just now"
        project["metadata"] = {"last_updated": last_updated}
    if "chat_history" not in project["metadata"]:
        project["metadata"]["chat_history"] = []
    if "version_history" not in project["metadata"]:
        project["metadata"]["version_history"] = [
            {
                "version": 1,
                "description": "Initial Multi-Agent Generation",
                "timestamp": datetime.now().isoformat(),
                "deliverables": project.get("deliverables", {}).copy()
            }
        ]

    chat_history = project["metadata"]["chat_history"]
    pending_changes = project["metadata"].get("pending_changes")
    pending_approval = project["metadata"].get("pending_approval")
    pending_impact = project["metadata"].get("pending_impact")

    # Render history
    render_chat_history(chat_history)

    # Render pending flow
    if pending_impact:
        render_pending_impact(project, pending_impact)
    elif pending_approval:
        render_pending_approval(project, pending_approval)
    elif pending_changes:
        render_pending_changes(project, pending_changes)

    # Render starters if empty
    if len(chat_history) <= 2 and not (pending_changes or pending_approval or pending_impact):
        render_starter_prompts()

    # Chat Input Box
    user_input = st.chat_input(
        placeholder="Type a message or edit request..." if not (pending_changes or pending_approval or pending_impact) else "Please confirm, review, or cancel the pending refinements first...",
        disabled=bool(pending_changes or pending_approval or pending_impact)
    )

    triggered_input = None
    if "selected_starter" in st.session_state:
        triggered_input = st.session_state.pop("selected_starter")
    elif user_input:
        triggered_input = user_input

    if triggered_input:
        with st.spinner("PM Agent is analyzing your request..."):
            try:
                from backend.agents.workspace_chat import chat_refine_workspace
                res = chat_refine_workspace(
                    workspace=project,
                    chat_history=chat_history,
                    user_message=triggered_input
                )
                project["deliverables"] = res["deliverables"]
                project["metadata"] = res["metadata"]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to refine workspace: {e}")

    # Version history control panel
    render_version_history(project)
