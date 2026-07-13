import streamlit as st
import time
import copy
from typing import Dict, Any

def render_version_history(project: Dict[str, Any]) -> None:
    """Renders the Version History control panel with timeline details, comparison diffs, and rollback triggers."""
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
                    st.markdown(f"**Author:** `{ver.get('author', 'ProductPilot')}`")
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
                            
                        # Check modified documents and display line-by-line diffs
                        import difflib
                        import json
                        
                        st.markdown("### 📝 Changes Summary")
                        has_diffs = False
                        for doc in common_docs:
                            content_a = ws_a["deliverables"][doc].get("content", ws_a["deliverables"][doc])
                            content_b = ws_b["deliverables"][doc].get("content", ws_b["deliverables"][doc])
                            
                            # Convert dict/list contents to JSON strings for comparison
                            if isinstance(content_a, (dict, list)):
                                str_a = json.dumps(content_a, indent=2)
                            else:
                                str_a = str(content_a)
                                
                            if isinstance(content_b, (dict, list)):
                                str_b = json.dumps(content_b, indent=2)
                            else:
                                str_b = str(content_b)
                                
                            if str_a != str_b:
                                has_diffs = True
                                st.markdown(f"#### 📄 Diff for **{doc}**")
                                diff_lines = list(difflib.unified_diff(
                                    str_a.splitlines(),
                                    str_b.splitlines(),
                                    fromfile=f"Version {v_a}",
                                    tofile=f"Version {v_b}",
                                    lineterm=""
                                ))
                                if diff_lines:
                                    diff_text = "\n".join(diff_lines)
                                    st.code(diff_text, language="diff")
                                    
                        if not has_diffs:
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
                            
                            # Log rollback version using VersionControl
                            from backend.version_history import VersionControl
                            restored_ws = VersionControl.create_version(
                                restored_ws,
                                action=f"Rollback to Version {restore_ver_num}",
                                summary=f"Restored workspace state back to historical Version {restore_ver_num}.",
                                author="User"
                            )
                            
                            active_id = st.session_state.get('active_project_id')
                            st.session_state['projects'][active_id] = restored_ws
                            st.success(f"🎉 Workspace successfully restored to Version {restore_ver_num}!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Rollback failed: {e}")
