import streamlit as st
from typing import Dict, Any

PRIORITY_COLOURS = {
    "Critical": "#FF3B3B",
    "High":     "#FF8C00",
    "Medium":   "#4F8CFF",
    "Low":      "#6B7280",
}

STATUS_COLOURS = {
    "To Do":       "#6B7280",
    "In Progress":  "#4F8CFF",
    "Blocked":     "#FF3B3B",
    "Done":        "#22C55E",
    "Draft":       "#A855F7",
    "Ready":       "#22C55E",
}

COMPLEXITY_COLOURS = {
    "Low":    "#22C55E",
    "Medium": "#FF8C00",
    "High":   "#FF3B3B",
}

RISK_COLOURS = {
    "Low":    "#22C55E",
    "Medium": "#FF8C00",
    "High":   "#FF3B3B",
}

def _badge(label: str, colour: str, bg_alpha: str = "22") -> str:
    """Returns an inline HTML badge/pill for the given label and colour."""
    return (
        f"<span style='display:inline-block; padding:2px 10px; border-radius:12px; "
        f"font-size:0.75rem; font-weight:600; color:{colour}; "
        f"background:{colour}{bg_alpha}; border:1px solid {colour}44; margin-right:5px;'>"
        f"{label}</span>"
    )

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
