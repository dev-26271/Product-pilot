import streamlit as st
from typing import Dict, Any

def render_export_center(project: Dict[str, Any]) -> None:
    """Renders the Export Center interface to configure and download file exports."""
    st.markdown("<h3 style='color: #F0F0F0; font-weight: 700; margin-bottom: 0.25rem;'>Export Center</h3>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.82rem; color: #9E9E9E; margin-bottom: 1.25rem;'>Export documents into PDF, DOCX, Markdown, or JSON without regenerating.</p>", unsafe_allow_html=True)
    
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

    # 4. Portable Workspace Backup Section
    st.markdown("<hr style='border-color: #374151; margin-top: 2rem; margin-bottom: 2rem;'>", unsafe_allow_html=True)
    st.markdown("#### 📦 Download Portable Workspace Backup (.json)")
    st.markdown("<p style='font-size: 0.82rem; color: #9E9E9E;'>Generate a complete backup package of this workspace. This will include all generated deliverables, uploaded files, vector store index, and document manifest. You can restore this project on any other instance by uploading it via the sidebar.</p>", unsafe_allow_html=True)
    
    if st.button("Compile Backup Package", type="secondary", use_container_width=True):
        with st.spinner("Packaging workspace artifacts and indexes..."):
            try:
                import json
                pkg = ExportService.export_workspace_package(project)
                pkg_json = json.dumps(pkg, indent=2, default=str)
                st.success("Backup package compiled successfully!")
                st.download_button(
                    label="💾 Download Workspace Backup JSON",
                    data=pkg_json,
                    file_name=f"{project.get('name', 'Project')}_backup.json",
                    mime="application/json",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Failed to package workspace: {e}")
