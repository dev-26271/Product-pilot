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
    pending_approval = project["metadata"].get("pending_approval")

    # 2. Display Chat Messages
    chat_container = st.container()
    with chat_container:
        for msg in chat_history:
            role = msg["role"]
            content = msg["content"]
            with st.chat_message(role):
                st.markdown(content)

    # 3. Render Pending Changes or Pending Approvals Summary if detected
    
    if pending_approval:
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

    # 4. Chat Input Box (Disabled if pending changes or approvals are awaiting confirmation)
    user_input = st.chat_input(
        placeholder="Type a message or edit request..." if not (pending_changes or pending_approval) else "Please confirm, approve, or cancel the pending refinements first...",
        disabled=bool(pending_changes or pending_approval)
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



