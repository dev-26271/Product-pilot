import streamlit as st
from typing import Dict, Any, List

def render_roadmap_entities(phases: List[Dict[str, Any]]) -> None:
    """Renders the canonical Roadmap phases into an interactive timeline UI."""
    if not phases:
        st.warning("No Roadmap phases found.")
        return

    st.markdown("### 🗓️ Phased Product Roadmap")
    for ph in phases:
        phase_id = ph.get("id", "SP-XXX")
        phase_name = ph.get("phase", "Phase")
        quarter = ph.get("quarter", "")
        objs = ph.get("objectives", [])
        objs_str = "".join(f"<li>{o}</li>" for o in objs)
        milestones = ph.get("milestones", [])
        miles_str = "".join(
            f"<li><strong>{m['date']}</strong>: {m['description']}</li>" if isinstance(m, dict) else f"<li>{m}</li>"
            for m in milestones
        )
        gngo = ph.get("go_no_go_criteria", [])
        gngo_str = "".join(f"<li>{c}</li>" for c in gngo)
        
        st.markdown(f"""
            <div style='border: 1px solid #2D2D2D; border-radius: 8px; padding: 1.25rem; background-color: #111827; margin-bottom: 1rem;'>
                <div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;'>
                    <span style='font-size:1.15rem; font-weight:700; color:#F5F5F5;'>{phase_id} — {phase_name} ({quarter})</span>
                    <span style='background:#A855F722; color:#A855F7; font-size:0.75rem; padding:3px 9px; border-radius:12px; font-weight:600;'>{ph.get('status', 'Planned')}</span>
                </div>
                <hr style='border-top:1px solid #2D2D2D; margin:0.8rem 0;'>
                <div style='font-size:0.88rem; color:#D1D5DB;'>
                    <strong>Objectives:</strong>
                    <ul style='margin-top: 0.2rem; padding-left:1.2rem;'>{objs_str or '<li>N/A</li>'}</ul>
                    <strong>Milestones:</strong>
                    <ul style='margin-top: 0.2rem; padding-left:1.2rem;'>{miles_str or '<li>N/A</li>'}</ul>
                    <strong>Go/No-Go Launch Gates:</strong>
                    <ul style='margin-top: 0.2rem; padding-left:1.2rem;'>{gngo_str or '<li>N/A</li>'}</ul>
                    <div style='margin-top:0.5rem; font-size:0.78rem; color:#6B7280;'>
                        Confidence: {ph.get('confidence', '0.9')} | Priority Score: {ph.get('priority_score', 'N/A')}/10 | Risk: {ph.get('risk_score', 'N/A')}/10
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
