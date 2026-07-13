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
                persona  = story.get("persona", "")
                action   = story.get("action", "")
                value    = story.get("value", "")
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
                doc_data = project['deliverables'][map_name]

                # ── User Stories: structured JSON → dedicated board renderer ──────
                if tab_name == "User Stories":
                    # Agent stores the raw structured JSON at the top level.
                    # Support both flat {"epics":…,"stories":…} and wrapped {"content":…}
                    us_data = doc_data.get("content", doc_data)
                    render_user_stories(us_data)

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
    st.markdown("<h3 style='color: #F5F5F5; font-weight: 600; margin-bottom: 0.5rem;'>💬 Chat & Refinement Strategy</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 1.5rem;'>Ask questions about the deliverables or suggest edits (e.g., 'Add subscription billing', 'Target enterprise customers'). The PM Agent will detect dependencies and propose document updates.</p>", unsafe_allow_html=True)

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

    # 2. Display Chat Messages
    chat_container = st.container()
    with chat_container:
        for msg in chat_history:
            role = msg["role"]
            content = msg["content"]
            with st.chat_message(role):
                st.markdown(content)

    # 3. Render Pending Changes Summary if detected
    if pending_changes:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background-color: #1E1E1E; border-left: 4px solid #FF8C00; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem;'>
                <h5 style='color: #FF8C00; margin: 0 0 0.5rem 0; font-weight: 600;'>⚠️ Proposed Refinements Detected</h5>
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
                        # Sync updated workspace back to session state
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

    # 4. Chat Input Box (Disabled if pending changes are awaiting confirmation)
    user_input = st.chat_input(
        placeholder="Type a message or edit request..." if not pending_changes else "Please confirm or cancel the pending refinements first...",
        disabled=bool(pending_changes)
    )

    if user_input:
        with st.spinner("PM Agent is analyzing your request..."):
            try:
                from backend.agents.workspace_chat import chat_refine_workspace
                res = chat_refine_workspace(
                    workspace=project,
                    chat_history=chat_history,
                    user_message=user_input
                )
                # Sync response deliverables and metadata back to session state
                project["deliverables"] = res["deliverables"]
                project["metadata"] = res["metadata"]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to refine workspace: {e}")

    # 5. Version History Section
    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.expander("📜 Workspace Version History", expanded=False):
        for v in reversed(project["metadata"]["version_history"]):
            desc = v["description"]
            ts = v["timestamp"][:19].replace("T", " ")
            st.markdown(
                f"<div style='padding: 0.5rem 0; border-bottom: 1px solid #2A2A2A;'>"
                f"<span style='color: #4F8CFF; font-weight: 600;'>Version {v['version']}</span> "
                f"<span style='color: #9E9E9E; font-size: 0.8rem;'>({ts})</span>"
                f"<div style='font-size: 0.9rem; color: #F5F5F5; margin-top: 0.25rem;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True
            )



