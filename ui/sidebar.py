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
            # Multi-line format button with name & metadata status
            button_label = f"📁 {proj_name}\n{proj['metadata']}"
            if st.button(
                button_label, 
                key=f"proj_{proj_name}", 
                use_container_width=True, 
                type="primary" if is_active else "secondary"
            ):
                st.session_state['active_project_id'] = proj_name
                st.rerun()
                
        # Footer spacer
        st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

