import streamlit as st
import time
from pathlib import Path
from typing import Dict, Any

def render_knowledge_sources(project: Dict[str, Any]) -> None:
    """Renders the Knowledge Sources expander panel with separated ProductPilot vs Project knowledge."""
    from backend.agents.retrieval_service import RetrievalService, sanitize_project_id
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    project_id = project.get("name", "ProductPilot_Project")
    sanitized_id = sanitize_project_id(project_id)
    
    project_dir = base_dir / "knowledge_base" / "projects" / sanitized_id
    uploads_dir = project_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    upload_store_path = project_dir / "vector_store"
    
    with st.expander("📚 Knowledge Grounding", expanded=False):
        # Collect files
        global_files = []
        for kb_domain in ["business", "product"]:
            kb_path = base_dir / "knowledge_base" / kb_domain
            if kb_path.exists():
                for f in kb_path.glob("*"):
                    if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".txt", ".docx", ".json", ".csv"]:
                        global_files.append(f.name)
                        
        project_files = []
        if uploads_dir.exists():
            for f in uploads_dir.glob("*"):
                if f.is_file() and f.suffix.lower() in [".pdf", ".md", ".txt", ".docx", ".json", ".csv"]:
                    project_files.append(f.name)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='label'>📚 ProductPilot Knowledge</div>
                    <div class='value'>{len(global_files)}</div>
                    <div class='subtitle'>Global reference documents</div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
            if global_files:
                for name in global_files:
                    st.markdown(f"<div class='knowledge-file'><span class='file-icon'>📄</span>{name}</div>", unsafe_allow_html=True)
            else:
                st.caption("No global knowledge base files loaded.")
                
        with col2:
            st.markdown(f"""
                <div class='metric-card'>
                    <div class='label'>📁 Project Knowledge</div>
                    <div class='value'>{len(project_files)}</div>
                    <div class='subtitle'>Project-specific uploads</div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
            if project_files:
                for name in project_files:
                    st.markdown(f"<div class='knowledge-file'><span class='file-icon'>📎</span>{name}</div>", unsafe_allow_html=True)
            else:
                st.caption("No project-specific documents uploaded yet.")
            
        # File Uploader
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload PDF, DOCX, MD, TXT, JSON, or CSV to extend grounding context",
            type=["pdf", "docx", "md", "txt", "json", "csv"],
            key=f"rag_uploader_{project['name']}",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            target_path = uploads_dir / uploaded_file.name
            with open(target_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.success(f"'{uploaded_file.name}' saved to project knowledge.")
            
            with st.spinner("Embedding and indexing document..."):
                try:
                    RetrievalService.clear_cache(project_id=project_id)
                    rag_service = RetrievalService()
                    rag_service.ingest_documents(uploads_dir)
                    new_store = rag_service.build_vector_store()
                    
                    if new_store:
                        upload_store_path.parent.mkdir(parents=True, exist_ok=True)
                        new_store.save_local(str(upload_store_path))
                        st.success("Project knowledge index rebuilt.")
                        time.sleep(0.5)
                        st.rerun()
                except Exception as e:
                    st.error(f"Indexing error: {e}")

def render_rag_inspector() -> None:
    """Renders the dedicated diagnostic RAG Inspector Page with retrieval scores and citations."""
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
