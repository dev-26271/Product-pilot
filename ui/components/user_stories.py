import streamlit as st
from typing import Dict, Any, List
from ui.components.common import (
    _badge, PRIORITY_COLOURS, STATUS_COLOURS, COMPLEXITY_COLOURS, RISK_COLOURS
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
