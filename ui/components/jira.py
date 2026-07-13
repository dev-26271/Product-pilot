import streamlit as st
from typing import Dict, Any, List
from ui.components.common import _badge, PRIORITY_COLOURS, STATUS_COLOURS

def render_jira_entities(tasks: List[Dict[str, Any]]) -> None:
    """Renders canonical Jira Task entities grouped by type as a styled backlog board."""
    if not tasks:
        st.warning("No Jira tasks found.")
        return

    # Group by type
    by_type: Dict[str, List] = {}
    for task in tasks:
        ttype = task.get("type", "Other")
        by_type.setdefault(ttype, []).append(task)

    TYPE_ICONS = {
        "Frontend": "💻", "Backend": "⚙️", "Database": "💾",
        "API": "🔗", "Testing": "🧪", "DevOps": "🚀", "Documentation": "📝",
    }

    st.markdown("### 🎫 Engineering Backlog & Jira Tasks")
    
    for ttype in ["Frontend", "Backend", "Database", "API", "Testing", "DevOps", "Documentation"]:
        group = by_type.get(ttype, [])
        if not group:
            continue
            
        icon = TYPE_ICONS.get(ttype, "🎫")
        st.markdown(f"#### {icon} {ttype} Backlog ({len(group)} tasks)")
        
        for task in group:
            tid = task.get("id", "JT-XXX")
            title = task.get("title", "")
            desc = task.get("description", "")
            pri = task.get("priority", "Medium")
            est = task.get("estimate", {})
            hours = est.get("hours", "?")
            sp = est.get("story_points", "?")
            status = task.get("status", "To Do")
            
            pri_c = PRIORITY_COLOURS.get(pri, "#6B7280")
            stat_c = STATUS_COLOURS.get(status, "#6B7280")
            
            with st.expander(f"{tid} — {title} ({sp} SP / {hours}h)"):
                st.markdown(f"""
                    <div style='font-size: 0.88rem; color: #D1D5DB;'>
                        <p>{desc}</p>
                        <div style='display:flex; gap:10px; margin-bottom: 0.6rem;'>
                            Priority: {_badge(pri, pri_c)}
                            Status: {_badge(status, stat_c)}
                        </div>
                        <strong>Acceptance Criteria:</strong>
                        <ul style='margin-top:0.2rem; padding-left:1.2rem;'>
                            {"".join(f"<li>{a}</li>" for a in task.get("acceptance_criteria", [])) or '<li>N/A</li>'}
                        </ul>
                        <strong>Dependencies:</strong> {", ".join(task.get("dependencies", [])) or 'None'}<br>
                        <strong>Labels:</strong> {", ".join(task.get("labels", [])) or 'None'}<br>
                    </div>
                """, unsafe_allow_html=True)
