import streamlit as st
import copy
import time
from typing import Dict, Any

def render_workspace_dashboard() -> None:
    """Renders the comprehensive persistent AI Product Manager dashboard."""
    active_id = st.session_state.get('active_project_id')
    if active_id is None:
        st.warning("Please select or generate a project first to view the dashboard.")
        return
        
    project = st.session_state['projects'][active_id]
    metadata = project.get("metadata_context", {})
    planning = project.get("metadata", {}).get("planning_analysis", {})
    
    st.markdown(f"<h2 style='color: #F0F0F0; font-weight: 800; margin-top: 1rem;'>📊 {project['name']}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9E9E9E; font-size: 0.85rem; margin-bottom: 1.5rem;'>Planning metrics, maturity tracking, decision logs, and version control.</p>", unsafe_allow_html=True)
    
    # 1. Metric Cards Row
    col1, col2, col3 = st.columns(3)
    
    # Project Health
    val_report = metadata.get("validation_report", {})
    val_score = val_report.get("score", 1.0)
    duration_ms = val_report.get("duration_ms", 0)
    
    if not val_report:
        health_value = "Stable"
        subtitle = "No validation report yet"
    else:
        is_valid = val_report.get("valid", True)
        health_value = f"{'✓' if is_valid else '✗'} {val_score*100:.0f}%"
        subtitle = f"{'Passed' if is_valid else 'Issues found'} · {duration_ms}ms"
        
    with col1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='label'>Project Health</div>
                <div class='value'>{health_value}</div>
                <div class='subtitle'>{subtitle}</div>
            </div>
        """, unsafe_allow_html=True)
        
    # Total Decisions
    decisions_count = len(project.get("metadata", {}).get("decision_log", []))
    with col2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='label'>Logged Decisions</div>
                <div class='value'>{decisions_count}</div>
                <div class='subtitle'>Captured in audit trail</div>
            </div>
        """, unsafe_allow_html=True)
        
    # Active Version
    active_version = len(project.get("metadata", {}).get("version_history", []))
    with col3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='label'>Workspace Version</div>
                <div class='value'>v{active_version}.0</div>
                <div class='subtitle'>All history snapshotted</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # 2. Left and Right Layout blocks
    left_col, right_col = st.columns([5, 4])
    
    with left_col:
        # Progress Engine - Workspace Maturity
        st.markdown("### 📈 Workspace Maturity")
        
        # Use planning scores or defaults
        scores = planning.get("maturity_scores", {
            "idea": 1.0,
            "business": 0.8 if project.get("business_analysis") else 0.5,
            "requirements": 0.9 if project.get("prd") else 0.4,
            "architecture": 0.3 if "Product Roadmap" in project.get("deliverables", {}) else 0.1,
            "testing": 0.2 if "User Stories" in project.get("deliverables", {}) else 0.0
        })
        
        avg_maturity = int(sum(scores.values()) / len(scores) * 100)
        
        for k, val in scores.items():
            label = k.title()
            val_pct = int(val * 100)
            st.markdown(f"""
                <div style='margin-bottom: 0.8rem;'>
                    <div style='display: flex; justify-content: space-between; font-size: 0.85rem; color: #D1D5DB; margin-bottom: 0.25rem;'>
                        <span>{label}</span>
                        <span>{val_pct}%</span>
                    </div>
                    <div style='background-color: #2D2D2D; width: 100%; height: 8px; border-radius: 4px;'>
                        <div style='background-color: #4F8CFF; width: {val_pct}%; height: 100%; border-radius: 4px;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown(f"""
            <div style='margin-top: 1rem; background-color: #4F8CFF11; border: 1px solid #4F8CFF33; border-radius: 6px; padding: 0.75rem; text-align: center;'>
                <strong style='color: #4F8CFF; font-size: 1.1rem;'>Overall Maturity Score: {avg_maturity}%</strong>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Decision Log
        st.markdown("### 📜 Decision Log & Audit Trail")
        decision_log = project.get("metadata", {}).get("decision_log", [])
        if decision_log:
            for dec in reversed(decision_log):
                ts = dec["timestamp"][:19].replace("T", " ")
                affected_docs_str = ", ".join([d.replace("_", " ").title() for d in dec["affected_documents"]])
                st.markdown(f"""
                    <div style='background-color: #1E1E1E; padding: 1rem; border-radius: 6px; border: 1px solid #2A2A2A; margin-bottom: 0.75rem;'>
                        <div style='display: flex; justify-content: space-between; font-size: 0.8rem; color: #9CA3AF;'>
                            <strong>ID: {dec['id']} ({dec['agent']})</strong>
                            <span>{ts}</span>
                        </div>
                        <div style='font-size: 0.9rem; color: #F5F5F5; margin-top: 0.4rem;'>{dec['reason']}</div>
                        <div style='font-size: 0.75rem; color: #4F8CFF; margin-top: 0.4rem;'>Affected: {affected_docs_str}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("*No modifications logged yet. Refine the project workspace via chat to log decisions.*")
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Human Approval interceptor in Dashboard
        pending_approval = project["metadata"].get("pending_approval")
        if pending_approval:
            st.markdown("### 🛡️ Pending Approvals")
            st.markdown(f"""
                <div style='background-color: #1A1A1A; border: 1px solid #FF4B4B; border-left: 4px solid #FF4B4B; padding: 1.2rem; border-radius: 6px; margin-bottom: 1rem;'>
                    <strong style='color: #FF4B4B; font-size: 0.95rem;'>Destructive scope change waiting for confirmation:</strong>
                    <p style='color: #E5E7EB; font-size: 0.88rem; margin: 0.5rem 0;'>"{pending_approval['instruction']}"</p>
                    <div style='font-size: 0.78rem; color: #9CA3AF;'>Impact: {pending_approval['impact']}</div>
                </div>
            """, unsafe_allow_html=True)
            col_app, col_rej = st.columns(2)
            with col_app:
                if st.button("Approve Refinements", key="dash_approve_btn", type="primary", use_container_width=True):
                    with st.spinner("Applying critical updates..."):
                        try:
                            from backend.agents.workspace_chat import apply_workspace_refinements
                            updated_workspace = apply_workspace_refinements(
                                workspace_dict=project,
                                instruction=pending_approval["instruction"],
                                affected_flags=pending_approval["affected"]
                            )
                            st.session_state['projects'][active_id] = updated_workspace
                            st.success("Refinements applied!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error applying updates: {e}")
            with col_rej:
                if st.button("Reject Refinements", key="dash_reject_btn", type="secondary", use_container_width=True):
                    project["metadata"].pop("pending_approval", None)
                    st.success("Proposed refinements cancelled.")
                    time.sleep(1)
                    st.rerun()
                    
    with right_col:
        # Smart Recommendations / Next Actions
        st.markdown("### 💡 Recommended Actions")
        actions = planning.get("recommended_actions", [
            "Generate Technical Architecture Plan",
            "Define User Journey specifications",
            "Refine weak metrics in Goals segment"
        ])
        for act in actions:
            st.markdown(f"✅ {act}")
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Smart Recommendations
        st.markdown("### 🧠 Smart Recommendations")
        recs = planning.get("smart_recommendations", [
            {"type": "Missing KPI", "description": "Ensure every goal maps to an engineering team performance index."},
            {"type": "Weak Acceptance Criteria", "description": "FR-002 lacks detail on fallback behaviors during server disconnects."}
        ])
        for rec in recs:
            st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 0.8rem; border-radius: 4px; margin-bottom: 0.5rem; border-left: 3px solid #EAB308;'>
                    <strong style='font-size: 0.8rem; color: #EAB308;'>{rec['type']}</strong>
                    <div style='font-size: 0.85rem; color: #D1D5DB; margin-top: 0.2rem;'>{rec['description']}</div>
                </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Rollback & Versioning Controls
        st.markdown("### 🔄 Version Rollback")
        versions = project.get("metadata", {}).get("version_history", [])
        if versions:
            ver_options = [f"v{v['version']}.0 - {v['description']}" for v in versions]
            selected_ver_str = st.selectbox("Select Version to Restore", ver_options, key="rollback_selector")
            
            if st.button("Rollback to Selected Version", type="secondary", use_container_width=True):
                ver_idx = ver_options.index(selected_ver_str)
                selected_version = versions[ver_idx]
                snapshot = selected_version.get("snapshot")
                if snapshot:
                    st.session_state['projects'][active_id] = copy.deepcopy(snapshot)
                    st.success(f"Successfully rolled back workspace to Version {selected_version['version']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("No complete snapshot was found for this older version log.")
        else:
            st.markdown("*No version snapshots available.*")
            
        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        
        # Execution Queue Panel
        st.markdown("### ⚙️ Execution Queue")
        queue_items = [
            {"job": "Intent Extraction", "status": "COMPLETED"},
            {"job": "Business Analysis", "status": "COMPLETED"},
            {"job": "Product Requirements Document (PRD)", "status": "COMPLETED"}
        ]
        
        for k in project.get("deliverables", {}).keys():
            if k not in ["Product Requirements Document (PRD)", "Business Analysis"]:
                queue_items.append({"job": k, "status": "COMPLETED"})
                
        for act in actions[:2]:
            if act not in project.get("deliverables", {}):
                queue_items.append({"job": act, "status": "QUEUED"})
                
        for item in queue_items:
            color = "#22C55E" if item["status"] == "COMPLETED" else "#EAB308"
            st.markdown(f"""
                <div style='display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.4rem 0; border-bottom: 1px solid #2D2D2D;'>
                    <span style='color: #F5F5F5;'>⚙️ {item['job']}</span>
                    <span style='color: {color}; font-weight: 600; font-size: 0.75rem;'>{item['status']}</span>
                </div>
            """, unsafe_allow_html=True)
            
    # 3. Visual Timeline
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown("### ⏳ Chronological Agent Execution Timeline")
    
    agent_logs = project.get("agent_logs", [])
    if agent_logs:
        timeline_html = "<div style='position: relative; padding-left: 1.5rem; border-left: 2px solid #2D2D2D;'>"
        for entry in agent_logs:
            ts = entry["timestamp"][:19].replace("T", " ")
            latency = entry.get("latency_ms", 0)
            timeline_html += f"""
                <div style='margin-bottom: 1.5rem; position: relative;'>
                    <div style='position: absolute; left: -1.95rem; top: 0.2rem; width: 12px; height: 12px; border-radius: 60%; background-color: #4F8CFF; border: 2px solid #121212;'></div>
                    <strong style='color: #F5F5F5; font-size: 0.95rem;'>{entry['agent']}</strong>
                    <span style='color: #9CA3AF; font-size: 0.75rem; margin-left: 10px;'>({ts})</span>
                    <div style='font-size: 0.82rem; color: #4F8CFF; margin-top: 0.15rem;'>
                        Model: {entry['model']} | Latency: {latency} ms
                    </div>
                </div>
            """
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)
    else:
        st.markdown("*No agent timeline logs recorded yet.*")
