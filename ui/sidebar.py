import streamlit as st

def render_sidebar() -> None:
    """Renders the workspace sidebar with persistent projects lists."""
    with st.sidebar:
        st.markdown("<div class='sidebar-title'>ProductPilot</div>", unsafe_allow_html=True)
        
        # New Project Action
        if st.button("＋ New Project", key="new_proj_btn", use_container_width=True, type="secondary"):
            st.session_state['active_project_id'] = None
            st.session_state['idea_input'] = ""
            # Reset all project configuration widgets to defaults
            st.session_state['cfg_industry'] = "Auto Detect"
            st.session_state['cfg_product_type'] = "Auto Detect"
            st.session_state['cfg_audience'] = "Auto Detect"
            st.session_state['cfg_deliverable'] = "Product Requirements Document (PRD)"
            st.session_state['cfg_detail_level'] = "Standard"
            st.session_state['cfg_risk'] = True
            st.rerun()
            
        # Navigation Section
        st.markdown("<div class='sidebar-section-header'>Navigation</div>", unsafe_allow_html=True)
        st.selectbox("Select View", ["Workspace", "Dashboard", "Traceability Explorer", "RAG Inspector"], key="nav_page_selection")
        
        # Projects Section
        st.markdown("<div class='sidebar-section-header'>Projects</div>", unsafe_allow_html=True)
        for proj_name in st.session_state['projects'].keys():
            proj = st.session_state['projects'][proj_name]
            is_active = st.session_state['active_project_id'] == proj_name
            # Safely extract last updated status from metadata dictionary or string
            meta_info = proj.get("metadata", "")
            if isinstance(meta_info, dict):
                status_text = meta_info.get("last_updated", "Updated just now")
            else:
                status_text = str(meta_info)
                
            button_label = f"📁 {proj_name}\n{status_text}"
            if st.button(
                button_label, 
                key=f"proj_{proj_name}", 
                use_container_width=True, 
                type="primary" if is_active else "secondary"
            ):
                st.session_state['active_project_id'] = proj_name
                st.rerun()
                
        # Import Workspace Section
        st.markdown("<div class='sidebar-section-header'>Import Workspace</div>", unsafe_allow_html=True)
        import_file = st.file_uploader(
            "Upload workspace .json package:",
            type=["json"],
            key="workspace_import_uploader",
            label_visibility="collapsed"
        )
        if import_file is not None:
            try:
                import json
                from backend.export_service import ExportService
                package = json.loads(import_file.read().decode("utf-8"))
                restored_ws = ExportService.import_workspace_package(package)
                proj_name = restored_ws["name"]
                st.session_state['projects'][proj_name] = restored_ws
                st.session_state['active_project_id'] = proj_name
                st.success(f"Workspace '{proj_name}' imported successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Import failed: {e}")

        # Footer spacer
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

