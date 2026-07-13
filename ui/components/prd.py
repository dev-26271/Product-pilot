import streamlit as st
from typing import Dict, Any

def render_prd_entities(prd_data: Dict[str, Any]) -> None:
    """Renders the canonical PRD entities into a beautiful human-readable layout."""
    if not prd_data:
        st.warning("No PRD data found.")
        return

    # Executive Summary Card
    ex = prd_data.get("Executive_Summary", {})
    if isinstance(ex, dict):
        st.markdown("### 🎯 Executive Summary")
        st.markdown(f"""
            <div style='background-color: #111827; padding: 1.25rem; border-radius: 10px; border: 1px solid #1F2937; margin-bottom: 1.5rem;'>
                <div style='margin-bottom: 0.8rem;'><strong style='color:#F5F5F5;'>Problem:</strong> <span style='color:#D1D5DB;'>{ex.get('problem', 'N/A')}</span></div>
                <div style='margin-bottom: 0.8rem;'><strong style='color:#F5F5F5;'>Opportunity:</strong> <span style='color:#D1D5DB;'>{ex.get('opportunity', 'N/A')}</span></div>
                <div style='margin-bottom: 0.8rem;'><strong style='color:#F5F5F5;'>Market Strategy:</strong> <span style='color:#D1D5DB;'>{ex.get('strategy', 'N/A')}</span></div>
                <div style='margin-bottom: 0.8rem;'><strong style='color:#F5F5F5;'>Timeline:</strong> <span style='color:#D1D5DB;'>{ex.get('timeline', 'N/A')}</span></div>
                <div style='margin-bottom: 0.8rem;'><strong style='color:#F5F5F5;'>Investment Summary:</strong> <span style='color:#D1D5DB;'>{ex.get('investment_summary', 'N/A')}</span></div>
            </div>
        """, unsafe_allow_html=True)
    
    # Product Vision
    vision = prd_data.get("Product_Vision", "")
    if vision:
        st.markdown("### 🔭 Product Vision")
        st.markdown(f"""
            <div style='background-color: #1E293B; border-left: 4px solid #4F8CFF; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem; color: #D1D5DB; font-style: italic;'>
                "{vision}"
            </div>
        """, unsafe_allow_html=True)
        
    # Personas Grid
    personas = prd_data.get("User_Personas", [])
    if personas:
        st.markdown("### 👥 User Personas")
        cols = st.columns(len(personas))
        for idx, p in enumerate(personas):
            with cols[idx]:
                pname = p.get("name", "User Persona")
                pid = p.get("id", f"PE-{idx+1}")
                prole = p.get("role", "")
                pgoals = p.get("goals", [])
                pgoals_str = "".join(f"<li>{g}</li>" for g in pgoals)
                pfru = p.get("pain_points") or p.get("frustrations") or []
                pfru_str = "".join(f"<li>{f}</li>" for f in pfru)
                st.markdown(f"""
                    <div style='background-color: #0F172A; border: 1px solid #1F2937; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <strong style='color: #F5F5F5; font-size:1.05rem;'>{pname}</strong>
                            <span style='background:#4F8CFF22; color:#4F8CFF; font-size:0.75rem; padding:2px 8px; border-radius:10px;'>{pid}</span>
                        </div>
                        <div style='color: #9CA3AF; font-size: 0.8rem; margin-top: 0.2rem; font-style: italic;'>{prole}</div>
                        <hr style='border-top:1px solid #2D2D2D; margin:0.6rem 0;'>
                        <div style='font-size:0.8rem; color:#D1D5DB;'>
                            <strong>Core Goals:</strong>
                            <ul style='margin: 0.2rem 0; padding-left: 1.1rem;'>{pgoals_str or '<li>N/A</li>'}</ul>
                            <strong>Frustrations:</strong>
                            <ul style='margin: 0.2rem 0; padding-left: 1.1rem;'>{pfru_str or '<li>N/A</li>'}</ul>
                            <strong>Technical Proficiency:</strong> {p.get('technical_proficiency', 'Medium')}<br>
                            <strong>Workflow:</strong> {p.get('daily_workflow') or p.get('workflow', 'N/A')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
    # Features List
    features = prd_data.get("Core_Features", [])
    if features:
        st.markdown("### ✨ Core Features")
        for f in features:
            fid = f.get("id", "FT-XXX")
            fname = f.get("name", "Feature")
            fdesc = f.get("description", "")
            fpersona = f.get("user_persona") or f.get("user_persona_mapping", "N/A")
            fval = f.get("business_value") or "N/A"
            
            fmetrics_raw = f.get("success_metrics") or f.get("success_metric") or []
            if isinstance(fmetrics_raw, str):
                fmetrics = fmetrics_raw
            elif isinstance(fmetrics_raw, list):
                fmetrics = ", ".join(fmetrics_raw)
            else:
                fmetrics = "N/A"
            
            with st.expander(f"⚙️ {fid} — {fname} ({f.get('priority', 'Medium')})"):
                st.markdown(f"""
                    <div style='font-size: 0.9rem; color: #D1D5DB;'>
                        <p>{fdesc}</p>
                        <strong>User Persona:</strong> {fpersona}<br>
                        <strong>Business Value:</strong> {fval}<br>
                        <strong>Success Metrics:</strong> {fmetrics}<br>
                        <strong>Confidence:</strong> {f.get('confidence', '0.9')}<br>
                        <strong>Risk Score:</strong> {f.get('risk_score', 'N/A')}/10
                    </div>
                """, unsafe_allow_html=True)

    # Functional Requirements List
    frs = prd_data.get("Functional_Requirements", [])
    if frs:
        st.markdown("### ⚙️ Functional Requirements")
        for fr in frs:
            frid = fr.get("id", "FR-XXX")
            title = fr.get("title") or fr.get("name") or "Requirement"
            desc = fr.get("description", "")
            
            ac_list = fr.get("acceptance_criteria", [])
            if isinstance(ac_list, str):
                ac_list = [ac_list]
            elif not isinstance(ac_list, list):
                ac_list = []
            ac_str = "".join(f"<li>{ac}</li>" for ac in ac_list)
            
            edge_cases = fr.get('edge_cases', [])
            if isinstance(edge_cases, str):
                edge_cases = [edge_cases]
            elif not isinstance(edge_cases, list):
                edge_cases = []
                
            deps = fr.get('dependencies', [])
            if isinstance(deps, str):
                deps = [deps]
            elif not isinstance(deps, list):
                deps = []
            
            with st.expander(f"📋 {frid} — {title} ({fr.get('priority', 'Medium')})"):
                st.markdown(f"""
                    <div style='font-size: 0.9rem; color: #D1D5DB;'>
                        <p>{desc}</p>
                        <strong>Acceptance Criteria:</strong>
                        <ul style='margin-top: 0.2rem; padding-left: 1.2rem;'>{ac_str or '<li>N/A</li>'}</ul>
                        <strong>Business Value:</strong> {fr.get('business_value', 'N/A')}<br>
                        <strong>User Persona:</strong> {fr.get('user_persona') or fr.get('user_persona_mapping', 'N/A')}<br>
                        <strong>Edge Cases:</strong> {", ".join(edge_cases) or 'None'}<br>
                        <strong>Dependencies:</strong> {", ".join(deps) or 'None'}<br>
                    </div>
                """, unsafe_allow_html=True)

    # Non-Functional Requirements
    nfrs = prd_data.get("Non_Functional_Requirements", {})
    if nfrs:
        st.markdown("### ⚙️ Non-Functional Requirements")
        nfr_cols = st.columns(2)
        items = list(nfrs.items())
        for idx, (n_title, n_desc) in enumerate(items):
            col = nfr_cols[idx % 2]
            with col:
                st.markdown(f"""
                    <div style='background-color: #1E1E1E; padding: 1rem; border-radius: 6px; border: 1px solid #2A2A2A; margin-bottom: 0.75rem;'>
                        <strong style='color: #4F8CFF; font-size: 0.9rem;'>{n_title}</strong>
                        <div style='color: #D1D5DB; font-size: 0.85rem; margin-top: 0.25rem;'>{n_desc}</div>
                    </div>
                """, unsafe_allow_html=True)
