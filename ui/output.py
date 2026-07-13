import streamlit as st
import time
from typing import Dict, Any, List


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


# ── Priority / Status colour palette ─────────────────────────────────────────
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


def render_user_stories(doc_data: Dict[str, Any]) -> None:
    """Renders the structured User Story JSON as a Linear / Jira-style board.

    Epics are collapsible expanders. Each story renders as a styled issue card
    with badges for Priority, Status, Story Points, Complexity, and Release.
    Acceptance Criteria are rendered as checkboxes. Dependencies are chips.
    Traceability is in a nested collapsible section. Raw JSON is never shown.
    """
    epics: List[Dict] = doc_data.get("epics", [])
    stories: List[Dict] = doc_data.get("stories", [])

    if not epics and not stories:
        st.warning("No Epics or Stories found in the generated output.")
        return

    # Build lookup: epic_id → list of stories
    epic_story_map: Dict[str, List[Dict]] = {}
    for story in stories:
        eid = story.get("epic_id", "uncategorised")
        epic_story_map.setdefault(eid, []).append(story)

    # ── Summary strip ─────────────────────────────────────────────────────────
    col_e, col_s, col_sp = st.columns(3)
    col_e.metric("Epics",   len(epics))
    col_s.metric("Stories", len(stories))
    total_sp = sum(s.get("estimate", {}).get("story_points", 0) for s in stories)
    col_sp.metric("Total Story Points", total_sp)
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ── Render each Epic ──────────────────────────────────────────────────────
    for epic in epics:
        eid    = epic.get("id", "?")
        etitle = epic.get("title", "Untitled Epic")
        edesc  = epic.get("description", "")
        eval_  = epic.get("business_value", "")
        erel   = epic.get("release", "")
        estat  = epic.get("status", "Draft")

        estat_c = STATUS_COLOURS.get(estat, "#6B7280")
        erel_c  = "#A855F7"

        epic_stories = epic_story_map.get(eid, [])
        story_count  = len(epic_stories)
        sp_total     = sum(s.get("estimate", {}).get("story_points", 0) for s in epic_stories)

        release_badge = _badge(erel, erel_c) if erel else ""
        bv_row = (
            f"<div style='margin-top:0.4rem; font-size:0.82rem; color:#4F8CFF;'>"
            f"<strong>Business Value:</strong> {eval_}</div>"
        ) if eval_ else ""
        desc_row = (
            f"<div style='margin-top:0.5rem; font-size:0.85rem; color:#9E9E9E;'>{edesc}</div>"
        ) if edesc else ""

        st.markdown(f"""
            <div style='border:1px solid #2A2A2A; border-radius:10px; padding:1rem 1.25rem;
                        background:#111827; margin-bottom:0.5rem;'>
                <div style='display:flex; align-items:center; gap:0.75rem; flex-wrap:wrap;'>
                    <span style='font-size:1.1rem; font-weight:700; color:#F5F5F5;'>{eid}</span>
                    <span style='font-size:1rem; font-weight:600; color:#E5E7EB;'>{etitle}</span>
                    {_badge(estat, estat_c)}
                    {release_badge}
                    <span style='margin-left:auto; font-size:0.8rem; color:#6B7280;'>
                        {story_count} stories · {sp_total} pts
                    </span>
                </div>
                {desc_row}
                {bv_row}
            </div>
        """, unsafe_allow_html=True)

        with st.expander(f"▸  Stories in {eid} — {etitle}  ({story_count})", expanded=True):
            if not epic_stories:
                st.markdown(
                    "<p style='color:#6B7280; font-size:0.85rem;'>No stories generated for this epic.</p>",
                    unsafe_allow_html=True
                )
                continue

            for story in epic_stories:
                sid      = story.get("id", "?")
                stitle   = story.get("title", "Untitled Story")
                feature  = story.get("feature", "")
                persona  = story.get("as_a") or story.get("persona", "")
                action   = story.get("i_want") or story.get("action", "")
                value    = story.get("so_that") or story.get("value", "")
                priority = story.get("priority", "Medium")
                status   = story.get("status", "To Do")
                risk     = story.get("risk", "Low")
                labels   = story.get("labels", [])
                deps     = story.get("dependencies", [])
                ac_list  = story.get("acceptance_criteria", [])
                trace    = story.get("traceability", {})
                estimate = story.get("estimate", {})
                sp       = estimate.get("story_points", "?")
                compl    = estimate.get("complexity", "?")

                pri_c   = PRIORITY_COLOURS.get(priority, "#6B7280")
                stat_c  = STATUS_COLOURS.get(status, "#6B7280")
                compl_c = COMPLEXITY_COLOURS.get(compl, "#6B7280")
                risk_c  = RISK_COLOURS.get(risk, "#6B7280")

                label_chips = " ".join(
                    f"<span style='display:inline-block; padding:1px 8px; border-radius:8px; "
                    f"font-size:0.7rem; color:#9CA3AF; background:#1F2937; border:1px solid #374151; "
                    f"margin-right:3px;'>{lbl}</span>"
                    for lbl in labels
                )
                label_row = f"<div style='margin-bottom:0.5rem;'>{label_chips}</div>" if label_chips else ""
                feature_row = (
                    f"<div style='font-size:0.78rem; color:#6B7280; margin-bottom:0.5rem;'>"
                    f"<strong>Feature:</strong> {feature}</div>"
                ) if feature else ""

                st.markdown(f"""
                    <div style='border:1px solid #1F2937; border-radius:8px; padding:1rem 1.25rem;
                                background:#0F172A; margin-bottom:0.75rem;'>

                        <div style='display:flex; align-items:flex-start; gap:0.75rem;
                                    flex-wrap:wrap; margin-bottom:0.6rem;'>
                            <span style='font-size:0.78rem; font-weight:700; color:#4F8CFF;
                                        white-space:nowrap;'>{sid}</span>
                            <span style='font-size:0.92rem; font-weight:600; color:#F9FAFB; flex:1;'>{stitle}</span>
                            {_badge(priority, pri_c)}
                            {_badge(status, stat_c)}
                            {_badge(f'{sp} pts', '#4F8CFF', '33')}
                            {_badge(compl, compl_c)}
                        </div>

                        {feature_row}

                        <div style='background:#1E293B; border-left:3px solid #4F8CFF;
                                    padding:0.5rem 0.75rem; border-radius:0 6px 6px 0;
                                    margin-bottom:0.6rem; font-size:0.85rem; color:#D1D5DB;'>
                            <strong>As a</strong> {persona},<br>
                            <strong>I want to</strong> {action},<br>
                            <strong>so that</strong> {value}.
                        </div>

                        {label_row}

                        <div style='font-size:0.77rem; color:#6B7280; margin-bottom:0.4rem;'>
                            Risk: {_badge(risk, risk_c)}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                # Acceptance Criteria — read-only checkboxes
                if ac_list:
                    st.markdown(
                        "<div style='font-size:0.82rem; font-weight:600; color:#9CA3AF; "
                        "margin-bottom:0.3rem; padding-left:0.25rem;'>✅ Acceptance Criteria</div>",
                        unsafe_allow_html=True
                    )
                    for ci, criterion in enumerate(ac_list):
                        st.checkbox(criterion, value=False, key=f"ac_{sid}_{ci}", disabled=True)
                    st.markdown("<div style='height:0.5rem;'/>", unsafe_allow_html=True)

                # Definition of Done — read-only checkboxes
                dod_list = story.get("definition_of_done", [])
                if dod_list:
                    st.markdown(
                        "<div style='font-size:0.82rem; font-weight:600; color:#9CA3AF; "
                        "margin-bottom:0.3rem; padding-left:0.25rem;'>📋 Definition of Done</div>",
                        unsafe_allow_html=True
                    )
                    for di, criterion in enumerate(dod_list):
                        st.checkbox(criterion, value=False, key=f"dod_{sid}_{di}", disabled=True)
                    st.markdown("<div style='height:0.5rem;'/>", unsafe_allow_html=True)

                # Dependencies — amber chips
                if deps:
                    dep_chips = " ".join(
                        f"<span style='display:inline-block; padding:2px 10px; border-radius:12px; "
                        f"font-size:0.75rem; color:#F59E0B; background:#F59E0B22; "
                        f"border:1px solid #F59E0B44; margin-right:4px;'>{d}</span>"
                        for d in deps
                    )
                    st.markdown(
                        f"<div style='font-size:0.82rem; font-weight:600; color:#9CA3AF; "
                        f"margin-bottom:0.5rem;'>🔗 Depends on: {dep_chips}</div>",
                        unsafe_allow_html=True
                    )

                # Traceability — collapsible
                frs = trace.get("functional_requirements", [])
                bgs = trace.get("business_goals", [])
                if frs or bgs:
                    with st.expander("🔍 Traceability", expanded=False):
                        if frs:
                            fr_chips = " ".join(
                                f"<span style='display:inline-block; padding:2px 9px; border-radius:10px; "
                                f"font-size:0.73rem; color:#22C55E; background:#22C55E22; "
                                f"border:1px solid #22C55E44; margin-right:4px;'>{fr}</span>"
                                for fr in frs
                            )
                            st.markdown(
                                f"<div style='font-size:0.8rem; margin-bottom:0.35rem;'>"
                                f"<strong style='color:#9CA3AF;'>Functional Requirements:</strong> {fr_chips}</div>",
                                unsafe_allow_html=True
                            )
                        if bgs:
                            bg_chips = " ".join(
                                f"<span style='display:inline-block; padding:2px 9px; border-radius:10px; "
                                f"font-size:0.73rem; color:#A855F7; background:#A855F722; "
                                f"border:1px solid #A855F744; margin-right:4px;'>{bg}</span>"
                                for bg in bgs
                            )
                            st.markdown(
                                f"<div style='font-size:0.8rem;'>"
                                f"<strong style='color:#9CA3AF;'>Business Goals:</strong> {bg_chips}</div>",
                                unsafe_allow_html=True
                            )

                st.markdown("<div style='height:0.4rem;'/>", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem;'/>", unsafe_allow_html=True)


def render_project_deliverables(project: Dict[str, Any]) -> None:

    """Renders document deliverables tabs dynamically showing compilation status."""
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

                # ── User Stories: structured JSON → dedicated board renderer ──────
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
                    # ── All other documents: generic section-by-section renderer ──
                    content = doc_data.get("content", doc_data)
                    for section_title, section_content in content.items():
                        st.markdown(f"""
                            <div class="prd-section">
                                <div class="prd-section-title">{section_title}</div>
                                <div class="prd-section-content">{str(section_content).replace(chr(10), '<br>')}</div>
                            </div>
                        """, unsafe_allow_html=True)


                # Targeted Refinement Section — not shown for User Stories (structured JSON)
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
                                    st.success(f"{tab_name} refined successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to refine {tab_name}: {e}")
                        else:
                            st.warning("Please provide a refinement instruction.")
            else:
                # Noncompiled State UI — shown when tab is opened but document not yet generated
                st.markdown("<div style='height: 2.5rem;'></div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style='text-align: center; color: #9E9E9E; padding: 4rem 2rem; border: 1px dashed #2A2A2A; border-radius: 10px;'>
                        <span style='font-size: 2rem; display: block; margin-bottom: 0.5rem;'>📄</span>
                        <h4 style='color: #F5F5F5; font-weight: 500; margin-bottom: 0.25rem;'>This document hasn't been generated yet.</h4>
                        <p style='font-size: 0.9rem;'>Generate it now?</p>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
                
                # Generate button — agent is ONLY called when user presses this
                col_l, col_m, col_r = st.columns([1.5, 2, 1.5])
                with col_m:
                    if st.button("Generate", key=f"lazy_gen_{tab_name}_{project['name']}", type="primary", use_container_width=True):
                        with st.spinner(f"Generating {tab_name}..."):
                            try:
                                generated_content = run_lazy_agent(tab_name, project)
                                # User Stories returns raw structured JSON — store directly.
                                # All other agents return a section dict — wrap in {"content": ...}.
                                if tab_name == "User Stories":
                                    project['deliverables'][map_name] = generated_content
                                else:
                                    project['deliverables'][map_name] = {
                                        "content": generated_content
                                    }
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed to generate {tab_name}: {e}")


def render_chat_refinement(project: Dict[str, Any]) -> None:
    """Renders the chat interface, dependency analyzer summary, confirmation, and version logs."""
    from datetime import datetime
    import streamlit as st
    
    st.markdown("<hr style='border-top: 1px solid #2A2A2A; margin: 3rem 0;'>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>💬 Ask ProductPilot</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1.5rem;'>Collaborate with a Senior Product Manager to understand, critique, explain, and incrementally modify your workspace deliverables. Ask questions, analyze tradeoffs, or request changes.</p>", unsafe_allow_html=True)

    # 1. Initialize metadata lists if not present
    if "metadata" not in project:
        project["metadata"] = {}
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

    # 2. Display Chat Messages
    chat_container = st.container()
    with chat_container:
        for msg in chat_history:
            role = msg["role"]
            content = msg["content"]
            with st.chat_message(role):
                st.markdown(content)
                
                # If Reasoning Trace is present in the assistant message, render it
                trace = msg.get("reasoning_trace")
                if trace and role == "assistant":
                    with st.expander("🔍 Reasoning Trace", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("<p style='font-size: 0.85rem; font-weight: 600; margin-bottom: 0.25rem; color: #E5E7EB;'>Sources Consulted</p>", unsafe_allow_html=True)
                            sources = trace.get("sources_consulted", [])
                            # Support both list of strings or string
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
                            # Handle string percentage or float
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

    # 3. Render Pending Changes or Pending Approvals Summary if detected
    
    if pending_impact:
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

    elif pending_approval:
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
                        # Sync updated workspace back to session state
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
        
    elif pending_changes:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background-color: #1E1E1E; border-left: 4px solid #FF8C00; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;'>
                <h5 style='color: #FF8C00; margin: 0 0 0.5rem 0; font-weight: 600;'>Proposed Refinements Detected</h5>
                <p style='color: #D1D5DB; font-size: 0.85rem; margin-bottom: 0.75rem;'>The PM Agent analyzed your request and detected the following document updates:</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Display list of changes
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

    # Render starter prompt grid when chat is fresh
    if len(chat_history) <= 2 and not (pending_changes or pending_approval or pending_impact):
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

    # 4. Chat Input Box (Disabled if pending changes, approvals, or impact analysis are awaiting confirmation)
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
                # Sync response deliverables and metadata back to session state
                project["deliverables"] = res["deliverables"]
                project["metadata"] = res["metadata"]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to refine workspace: {e}")

    # 5. Version History Section
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("📜 Workspace Version History & Control", expanded=False):
        version_history = project["metadata"].get("version_history", [])
        if not version_history:
            st.info("No version history available.")
        else:
            from backend.version_history import rebuild_workspace_version
            
            # Divide into tabs: Timeline & Details, Compare Versions, Version Rollback
            v_tabs = st.tabs(["🕒 Version Timeline", "🔄 Compare Versions", "🛡️ Rollback Control"])
            
            # --- Tab 1: Version Timeline & Details ---
            with v_tabs[0]:
                col_list, col_det = st.columns([2, 3])
                
                with col_list:
                    st.markdown("### 🕒 Versions")
                    version_options = [f"Version {v['version']}: {v['description'][:25]}..." for v in reversed(version_history)]
                    selected_ver_str = st.radio(
                        "Select Version to View Details:",
                        options=version_options,
                        key="selected_timeline_version"
                    )
                    
                    selected_ver_num = int(selected_ver_str.split(":")[0].replace("Version ", "").strip())
                    
                with col_det:
                    # Find selected version details
                    ver = next(v for v in version_history if v["version"] == selected_ver_num)
                    st.markdown(f"### 📄 Version {ver['version']} Details")
                    
                    ts = ver["timestamp"][:19].replace("T", " ")
                    st.markdown(f"**Timestamp:** `{ts}`")
                    st.markdown(f"**Action:** `{ver['description']}`")
                    
                    summary = ver.get("summary") or ver.get("description")
                    st.markdown(f"**Summary:** {summary}")
                    
                    # Changed documents
                    docs = ver.get("changed_documents", [])
                    st.markdown("**Changed Documents:**")
                    if docs:
                        st.markdown(" ".join([f"`{d}`" for d in docs]))
                    else:
                        st.markdown("*None or baseline*")
                        
                    # Modified entities
                    ents = ver.get("modified_entities", [])
                    st.markdown("**Modified Entities:**")
                    if ents:
                        st.markdown(" ".join([f"`{e}`" for e in ents]))
                    else:
                        st.markdown("*None or baseline*")
                        
                    # Validation status
                    val = ver.get("validation_status", {})
                    valid = val.get("valid", True) if isinstance(val, dict) else True
                    score = val.get("score", 1.0) if isinstance(val, dict) else 1.0
                    st.markdown(f"**Validation Status:** {'✅ Valid' if valid else '❌ Anomalous'} (Score: `{score}`)")
                    
                    # Show errors or warnings
                    if isinstance(val, dict):
                        errors = val.get("errors", [])
                        warnings = val.get("warnings", [])
                        if errors:
                            st.error(f"Errors: {', '.join(errors)}")
                        if warnings:
                            st.warning(f"Warnings: {', '.join(warnings)}")

            # --- Tab 2: Compare Versions ---
            with v_tabs[1]:
                st.markdown("### 🔄 Compare Two Versions")
                col_a, col_b = st.columns(2)
                
                v_nums = [v["version"] for v in version_history]
                with col_a:
                    v_a = st.selectbox("Version A (Base):", v_nums, index=0)
                with col_b:
                    v_b = st.selectbox("Version B (Compare):", v_nums, index=len(v_nums)-1)
                    
                if st.button("Compare Versions"):
                    try:
                        ws_a = rebuild_workspace_version(version_history, v_a)
                        ws_b = rebuild_workspace_version(version_history, v_b)
                        
                        st.markdown(f"#### 🔍 Comparing Version {v_a} vs. Version {v_b}")
                        
                        # Compare deliverables
                        docs_a = set(ws_a.get("deliverables", {}).keys())
                        docs_b = set(ws_b.get("deliverables", {}).keys())
                        
                        added_docs = docs_b - docs_a
                        removed_docs = docs_a - docs_b
                        common_docs = docs_a & docs_b
                        
                        if added_docs:
                            st.markdown(f"🟢 **Added Documents in B:** {', '.join(added_docs)}")
                        if removed_docs:
                            st.markdown(f"🔴 **Removed Documents in B:** {', '.join(removed_docs)}")
                            
                        # Check modified documents
                        modified_docs = []
                        for doc in common_docs:
                            if ws_a["deliverables"][doc] != ws_b["deliverables"][doc]:
                                modified_docs.append(doc)
                                
                        if modified_docs:
                            st.markdown(f"🟡 **Modified Documents:** {', '.join(modified_docs)}")
                        else:
                            st.markdown("⚪ **No document contents differed.**")
                            
                        # Compare validation scores
                        score_a = ws_a.get("metadata", {}).get("validation_report", {}).get("overall_score", 1.0)
                        score_b = ws_b.get("metadata", {}).get("validation_report", {}).get("overall_score", 1.0)
                        st.markdown(f"⚖️ **Validation Score:** Version A: `{score_a}` | Version B: `{score_b}`")
                        
                    except Exception as e:
                        st.error(f"Failed to compare versions: {e}")

            # --- Tab 3: Rollback Control ---
            with v_tabs[2]:
                st.markdown("### 🛡️ Restore Previous Version")
                st.warning("⚠️ Restoring a version will set the active project deliverables back to the state of that version. All history will be preserved.")
                
                restore_options = [f"Version {v['version']}: {v['description'][:40]}..." for v in version_history]
                restore_ver_str = st.selectbox(
                    "Select Target Restore Version:",
                    options=restore_options,
                    key="restore_version_selection"
                )
                
                restore_ver_num = int(restore_ver_str.split(":")[0].replace("Version ", "").strip())
                
                if st.button("Restore Version Now", type="primary"):
                    with st.spinner("Restoring workspace to selected version..."):
                        try:
                            # Rebuild and set as active project
                            restored_ws = rebuild_workspace_version(version_history, restore_ver_num)
                            
                            # Append a rollback history entry
                            new_version_num = len(version_history) + 1
                            rollback_entry = {
                                "version": new_version_num,
                                "description": f"Rollback to Version {restore_ver_num}",
                                "timestamp": datetime.now().isoformat(),
                                "modified_entities": [],
                                "changed_documents": [],
                                "validation_status": restored_ws.get("metadata", {}).get("validation_report", {}),
                                "summary": f"Restored workspace state back to historical Version {restore_ver_num}.",
                                "snapshot": restored_ws
                            }
                            # Save version list into metadata
                            restored_ws.setdefault("metadata", {})["version_history"] = version_history + [rollback_entry]
                            
                            active_id = st.session_state.get('active_project_id')
                            st.session_state['projects'][active_id] = restored_ws
                            st.success(f"🎉 Workspace successfully restored to Version {restore_ver_num}!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Rollback failed: {e}")


def render_knowledge_sources(project: Dict[str, Any]) -> None:
    """Renders the Knowledge Sources expander panel, showing loaded files, chunk statistics, and enabling document uploads."""
    import streamlit as st
    import time
    from pathlib import Path
    from backend.agents.retrieval_service import RetrievalService
    from langchain_community.vectorstores import FAISS
    from rag.embeddings import get_embeddings
    
    base_dir = Path(__file__).resolve().parent.parent
    uploads_dir = base_dir / "knowledge_base" / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    with st.expander("📚 Knowledge Grounding Sources", expanded=False):
        st.markdown("<p style='font-size:0.85rem; color:#9E9E9E;'>Inspect the enterprise knowledge base and upload additional files to ground requirements generation.</p>", unsafe_allow_html=True)
        
        # 1. Display list of loaded knowledge base files
        files_list = []
        for kb_domain in ["business", "product", "uploads"]:
            kb_path = base_dir / "knowledge_base" / kb_domain
            if kb_path.exists():
                for f in kb_path.glob("*"):
                    if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".txt", ".docx", ".json", ".csv"]:
                        files_list.append((f.name, kb_domain))
                        
        st.markdown("#### 📁 Active Knowledge Base Documents")
        if files_list:
            for name, domain in files_list:
                st.markdown(f"📄 **{name}** (Folder: `{domain}`)")
        else:
            st.markdown("*No files loaded inside knowledge_base folders.*")
            
        # 2. File Uploader component
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### 📤 Upload Grounding Documents")
        uploaded_file = st.file_uploader(
            "Upload PDF, DOCX, MD, TXT, JSON, or CSV to extend grounding context:",
            type=["pdf", "docx", "md", "txt", "json", "csv"],
            key=f"rag_uploader_{project['name']}"
        )
        
        if uploaded_file is not None:
            target_path = uploads_dir / uploaded_file.name
            with open(target_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.success(f"File '{uploaded_file.name}' saved to uploads directory!")
            
            # Re-build vector index for uploaded documents dynamically
            with st.spinner("Embedding document and rebuilding vector index..."):
                try:
                    embeddings = get_embeddings()
                    rag_service = RetrievalService()
                    rag_service.ingest_documents(uploads_dir)
                    new_store = rag_service.build_vector_store()
                    
                    if new_store:
                        upload_store_path = base_dir / "rag" / "vector_store" / "uploads"
                        new_store.save_local(str(upload_store_path))
                        st.success("Successfully rebuilt grounding vector index!")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"Error rebuilding vector store index: {e}")


def render_rag_inspector() -> None:
    """Renders the dedicated diagnostic RAG Inspector Page with retrieval scores and citations."""
    import streamlit as st
    
    st.markdown("<h2 style='color: #F5F5F5; font-weight: 600; margin-top: 1.5rem;'>🔍 RAG Grounding Inspector</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9E9E9E; font-size: 0.9rem; margin-bottom: 2rem;'>Inspect similarities, hybrid dense/keyword retrieval scores, cross-encoder rerank metrics, and citation sources.</p>", unsafe_allow_html=True)
    
    active_id = st.session_state.get('active_project_id')
    if active_id is None:
        st.warning("Please select or generate a project first to inspect its grounding context.")
        return
        
    project = st.session_state['projects'][active_id]
    rag_context = project.get("rag_context", [])
    
    if not rag_context:
        st.info("No grounding context has been retrieved yet for this project. Generate deliverables to run grounding.")
        return
        
    st.markdown(f"""
        <div style='background-color: #1A1A1A; border: 1px solid #2A2A2A; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;'>
            <strong>Grounding Target:</strong> {project['idea']}<br>
            <strong>Total Grounded Chunks:</strong> {len(rag_context)} sources mapped.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Retrieved Chunks & Rerank Scores")
    for idx, chunk in enumerate(rag_context):
        confidence = chunk.get("confidence", 0.0)
        source = chunk.get("metadata", {}).get("source", "Unknown Source")
        doc_type = chunk.get("metadata", {}).get("document_type", "txt")
        page = chunk.get("metadata", {}).get("page", 1)
        source_type = chunk.get("source_type", "dense")
        chunk_id = chunk.get("metadata", {}).get("chunk_id", "N/A")
        
        st.markdown(f"""
            <div style='background-color: #1E1E1E; border-left: 4px solid #4F8CFF; padding: 1.2rem; border-radius: 6px; margin-bottom: 1rem;'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                    <strong style='color: #F5F5F5; font-size: 0.95rem;'>Source: {source} (Page {page})</strong>
                    <span style='background-color: #4F8CFF22; color: #4F8CFF; padding: 2px 8px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>Score: {confidence:.2f}</span>
                </div>
                <p style='color: #D1D5DB; font-size: 0.88rem; margin: 0 0 0.5rem 0; font-family: monospace; white-space: pre-wrap;'>{chunk["content"]}</p>
                <div style='font-size: 0.75rem; color: #9E9E9E;'>
                    Type: {doc_type.upper()} | Method: {source_type.title()} | ID: {chunk_id}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
    st.markdown("### 📝 Final Prompt Context Injection")
    context_str = "\n\n".join([
        f"[Source: {c['metadata']['source']} Page {c['metadata']['page']}]\n{c['content']}"
        for c in rag_context
    ])
    st.text_area("Context Injected in System Prompts", value=context_str, height=250, disabled=True)


def render_workspace_dashboard() -> None:
    """Renders the comprehensive persistent AI Product Manager dashboard."""
    import streamlit as st
    import copy
    import time
    
    active_id = st.session_state.get('active_project_id')
    if active_id is None:
        st.warning("Please select or generate a project first to view the dashboard.")
        return
        
    project = st.session_state['projects'][active_id]
    metadata = project.get("metadata_context", {})
    planning = project.get("metadata", {}).get("planning_analysis", {})
    
    st.markdown(f"<h2 style='color: #F5F5F5; font-weight: 800; margin-top: 1.5rem;'>📊 Workspace Dashboard: {project['name']}</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9E9E9E; font-size: 0.9rem; margin-bottom: 2rem;'>Active planning metrics, maturity tracking, decision logs, execution queues, and version rollbacks.</p>", unsafe_allow_html=True)
    
    # 1. Metric Cards Row
    col1, col2, col3 = st.columns(3)
    
    # Project Health
    val_report = metadata.get("validation_report", {})
    val_score = val_report.get("score", 1.0)
    health_status = "Healthy 🟢" if val_score >= 0.8 else "Needs Optimization 🟡"
    if not val_report:
        health_status = "Stable 🟢"
        
    with col1:
        st.markdown(f"""
            <div style='background-color: #1E1E1E; padding: 1.2rem; border-radius: 6px; border: 1px solid #2A2A2A;'>
                <div style='font-size: 0.8rem; color: #9CA3AF; text-transform: uppercase;'>Project Health</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #F5F5F5; margin-top: 0.25rem;'>{health_status}</div>
                <div style='font-size: 0.75rem; color: #6B7280; margin-top: 0.25rem;'>Validation Score: {val_score*100:.0f}%</div>
            </div>
        """, unsafe_allow_html=True)
        
    # Total Decisions
    decisions_count = len(project.get("metadata", {}).get("decision_log", []))
    with col2:
        st.markdown(f"""
            <div style='background-color: #1E1E1E; padding: 1.2rem; border-radius: 6px; border: 1px solid #2A2A2A;'>
                <div style='font-size: 0.8rem; color: #9CA3AF; text-transform: uppercase;'>Logged Decisions</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #F5F5F5; margin-top: 0.25rem;'>{decisions_count} Updates</div>
                <div style='font-size: 0.75rem; color: #6B7280; margin-top: 0.25rem;'>Captured in Audit Trail</div>
            </div>
        """, unsafe_allow_html=True)
        
    # Active Version
    active_version = len(project.get("metadata", {}).get("version_history", []))
    with col3:
        st.markdown(f"""
            <div style='background-color: #1E1E1E; padding: 1.2rem; border-radius: 6px; border: 1px solid #2A2A2A;'>
                <div style='font-size: 0.8rem; color: #9CA3AF; text-transform: uppercase;'>Workspace Version</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: #F5F5F5; margin-top: 0.25rem;'>v{active_version}.0</div>
                <div style='font-size: 0.75rem; color: #6B7280; margin-top: 0.25rem;'>All history snapshotted</div>
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


def render_traceability_explorer() -> None:
    """Renders the Enterprise Traceability explorer dashboard with Mermaid graphs, search, coverage audit, and exports."""
    import streamlit as st
    import json
    from backend.agents.traceability_engine import TraceabilityEngine
    
    active_id = st.session_state.get('active_project_id')
    if active_id is None:
        st.warning("Please select or generate a project first to explore traceability.")
        return
        
    project = st.session_state['projects'][active_id]
    engine = TraceabilityEngine(project)
    
    st.markdown(f"<h2 style='color: #F5F5F5; font-weight: 800; margin-top: 1.5rem;'>🕸️ Traceability Matrix & Dependency Explorer</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #9E9E9E; font-size: 0.9rem; margin-bottom: 2rem;'>Map, search, and audit linkages between problem statements, goals, features, functional requirements, and stories.</p>", unsafe_allow_html=True)
    
    # 1. Coverage Warnings
    warnings = engine.check_coverage()
    if warnings:
        with st.expander(f"⚠️ Coverage Warnings & Quality Audits ({len(warnings)})", expanded=True):
            for w in warnings:
                st.markdown(f"🚨 **{w['category']}** ({w['item']}): {w['warning']}")
    else:
        st.success("✓ 100% Traceability and Coverage verified!")
        
    # 2. Export Actions Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 Export Traceability (CSV)",
            data=engine.export_csv(),
            file_name=f"{project['name']}_traceability_matrix.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col2:
        st.download_button(
            "📥 Export Dependency Graph (JSON)",
            data=json.dumps(engine.graph, indent=2),
            file_name=f"{project['name']}_dependency_graph.json",
            mime="application/json",
            use_container_width=True
        )
    with col3:
        # Build Coverage analysis text
        cov_text = "TRACEABILITY MATRIX COVERAGE REPORT\n==================================\n\n"
        if warnings:
            for w in warnings:
                cov_text += f"[{w['category']}] {w['item']}: {w['warning']}\n"
        else:
            cov_text += "All nodes covered. 100% trace complete."
        st.download_button(
            "📥 Export Coverage Report",
            data=cov_text,
            file_name=f"{project['name']}_coverage_report.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    
    # 3. Explorer split
    left_col, right_col = st.columns([4, 5])
    
    # Track selection in session state
    if "active_explorer_node" not in st.session_state:
        st.session_state["active_explorer_node"] = ""
        
    with left_col:
        st.markdown("### 🔍 Node Navigator")
        node_options = list(engine.graph["nodes"].keys())
        if node_options:
            selected_node = st.selectbox(
                "Search or select requirements node:",
                node_options,
                index=node_options.index(st.session_state["active_explorer_node"]) if st.session_state["active_explorer_node"] in node_options else 0,
                key="explorer_selectbox"
            )
            st.session_state["active_explorer_node"] = selected_node
        else:
            st.info("No nodes in the dependency graph yet.")
            selected_node = ""
            
        if selected_node:
            node = engine.graph["nodes"][selected_node]
            st.markdown(f"""
                <div style='background-color: #1E1E1E; padding: 1.2rem; border-radius: 6px; border-left: 4px solid #4F8CFF; margin-top: 1rem;'>
                    <div style='font-size: 0.8rem; color: #9CA3AF; text-transform: uppercase;'>{node['type']}</div>
                    <h4 style='color: #F5F5F5; margin: 0.25rem 0 0.75rem 0;'>{selected_node}</h4>
                    <p style='color: #E5E7EB; font-size: 0.9rem;'>{node['label']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Print Details
            st.markdown("##### Details:")
            st.json(node["details"])
            
            # Traversal links
            deps = engine.get_dependencies(selected_node)
            st.markdown("##### Forward Links (Dependents):")
            if deps["forward"]:
                for fn in deps["forward"]:
                    if st.button(f"➡️ Jump to {fn}", key=f"fw_{fn}"):
                        st.session_state["active_explorer_node"] = fn
                        st.rerun()
            else:
                st.markdown("*None*")
                
            st.markdown("##### Reverse Links (Traced Elements):")
            if deps["reverse"]:
                for rn in deps["reverse"]:
                    if st.button(f"⬅️ Jump to {rn}", key=f"rev_{rn}"):
                        st.session_state["active_explorer_node"] = rn
                        st.rerun()
            else:
                st.markdown("*None*")
                
    with right_col:
        st.markdown("### 🕸️ Interactive Mermaid Relationship Graph")
        
        # Build Mermaid code
        mermaid_code = "graph TD\n"
        # Style node definitions
        for nid, node in engine.graph["nodes"].items():
            clean_label = node["label"].replace('"', '').replace('[', '').replace(']', '').replace(':', ' -')
            clean_label = clean_label[:40] + "..." if len(clean_label) > 40 else clean_label
            # Highlight currently active selected node in graph
            if nid == selected_node:
                mermaid_code += f'    {nid}("{nid}: {clean_label}"):::selected\n'
            else:
                mermaid_code += f'    {nid}["{nid}: {clean_label}"]\n'
                
        for edge in engine.graph["edges"]:
            if edge["source"] in engine.graph["nodes"] and edge["target"] in engine.graph["nodes"]:
                mermaid_code += f'    {edge["source"]} -->|"{edge["relation"]}"| {edge["target"]}\n'
                
        # Define Selected highlighting style class
        mermaid_code += "    classDef selected fill:#4F8CFF22,stroke:#4F8CFF,stroke-width:2px,color:#4F8CFF;\n"
        
        st.markdown(f"```mermaid\n{mermaid_code}\n```")


def render_prd_entities(prd_data: Dict[str, Any]) -> None:
    """Renders the canonical PRD entities into a beautiful human-readable layout."""
    import streamlit as st
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
            fmetrics = ", ".join(f.get("success_metrics", []))
            
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
            title = fr.get("title", "Requirement")
            desc = fr.get("description", "")
            ac_list = fr.get("acceptance_criteria", [])
            ac_str = "".join(f"<li>{ac}</li>" for ac in ac_list)
            
            with st.expander(f"📋 {frid} — {title} ({fr.get('priority', 'Medium')})"):
                st.markdown(f"""
                    <div style='font-size: 0.9rem; color: #D1D5DB;'>
                        <p>{desc}</p>
                        <strong>Acceptance Criteria:</strong>
                        <ul style='margin-top: 0.2rem; padding-left: 1.2rem;'>{ac_str or '<li>N/A</li>'}</ul>
                        <strong>Business Value:</strong> {fr.get('business_value', 'N/A')}<br>
                        <strong>User Persona:</strong> {fr.get('user_persona', 'N/A')}<br>
                        <strong>Edge Cases:</strong> {", ".join(fr.get('edge_cases', [])) or 'None'}<br>
                        <strong>Dependencies:</strong> {", ".join(fr.get('dependencies', [])) or 'None'}<br>
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


def render_roadmap_entities(phases: List[Dict[str, Any]]) -> None:
    """Renders the canonical Roadmap phases into an interactive timeline UI."""
    import streamlit as st
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


def render_jira_entities(tasks: List[Dict[str, Any]]) -> None:
    """Renders canonical Jira Task entities grouped by type as a styled backlog board."""
    import streamlit as st
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


def render_export_center(project: Dict[str, Any]) -> None:
    """Renders the Export Center interface to configure and download file exports."""
    st.markdown("<h3 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>📤 Workspace Export Center</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1.5rem;'>Export your generated specifications, roadmaps, stories, and tasks into high-quality formats without regenerating any workspace documents.</p>", unsafe_allow_html=True)
    
    # 1. Select Export Scope
    scopes = [
        "Entire Workspace",
        "PRD",
        "BRD",
        "SRS",
        "User Stories",
        "Roadmap",
        "Jira Tasks",
        "Sprint Backlog",
        "Executive Summary"
    ]
    scope_sel = st.selectbox("Select Export Scope", scopes, index=0)
    
    # 2. Select Export Format
    formats = {
        "PDF Document (.pdf)": "pdf",
        "Word Document (.docx)": "docx",
        "Markdown Text (.md)": "md",
        "JSON Context Data (.json)": "json"
    }
    format_sel = st.selectbox("Select Export Format", list(formats.keys()), index=0)
    fmt_key = formats[format_sel]
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # 3. Export Action Button
    from backend.export_service import ExportService
    
    # Pre-check if content is generated
    scope_data = ExportService._resolve_scope_data(project, scope_sel)
    if not scope_data:
        st.warning(f"⚠️ Content for '{scope_sel}' is not yet generated. Please go to its respective tab to compile it first.")
        return
        
    expected_path = ExportService.get_export_filepath(project.get("name", "Project"), scope_sel, fmt_key)
    st.info(f"📂 **Export Destination:** `{expected_path}`")
    
    if st.button("Generate Export File", type="primary", use_container_width=True):
        with st.spinner("Compiling and generating export file..."):
            res = ExportService.export(project, scope_sel, fmt_key)
            if res.get("status") == "success":
                st.success(f"🎉 Export generated successfully!")
                
                # Load the binary/text data to feed into Streamlit download button
                try:
                    with open(res["location"], "rb") as f:
                        btn_data = f.read()
                        
                    st.download_button(
                        label=f"💾 Download {res['filename']}",
                        data=btn_data,
                        file_name=res["filename"],
                        mime="application/octet-stream",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Failed to read generated export: {e}")
            else:
                st.error(f"Failed to export: {res.get('error')}")



