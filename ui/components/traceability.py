import streamlit as st
import json
from typing import Dict, Any
from backend.agents.traceability_engine import TraceabilityEngine

def render_traceability_explorer() -> None:
    """Renders the Enterprise Traceability explorer dashboard with Mermaid graphs, search, coverage audit, and exports."""
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
