import streamlit as st
from typing import Tuple


def render_project_configuration() -> Tuple[str, str, str, str, str, bool]:
    """Renders the project configuration panel inside st.expander."""
    with st.expander("Project Configuration", expanded=False):
        st.markdown("<div style='font-size: 0.85rem; color: #9E9E9E; margin-bottom: 0.5rem; margin-top: -0.5rem;'>Configure how ProductPilot should generate documentation.</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 0.78rem; color: #7C8BF5; margin-bottom: 1rem;'>\u2728 <strong>Auto Detect</strong> infers Industry, Product Type, and Audience from your product idea using AI.</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            industry = st.selectbox(
                "Industry",
                options=["Auto Detect", "Healthcare", "Finance", "Education", "Retail", "Logistics", "Travel", "Real Estate", "HR", "Legal", "Entertainment", "Food & Beverage", "Agriculture", "Government", "Other"],
                key="cfg_industry"
            )
        with col2:
            product_type = st.selectbox(
                "Product Type",
                options=["Auto Detect", "SaaS Platform", "Mobile App", "AI Assistant", "Marketplace", "Dashboard", "Internal Tool", "API Platform", "Enterprise Software", "CRM", "Productivity Tool"],
                key="cfg_product_type"
            )
        with col3:
            audience = st.selectbox(
                "Audience",
                options=["Auto Detect", "B2B", "B2C", "Enterprise", "Internal", "Government"],
                key="cfg_audience"
            )
            
        col4, col5, col6 = st.columns(3)
        with col4:
            deliverable = st.selectbox(
                "Deliverable",
                options=[
                    "Product Requirements Document (PRD)",
                    "Business Requirements Document (BRD)",
                    "Software Requirements Specification (SRS)",
                    "Technical Design Document (TDD)",
                    "User Stories",
                    "Sprint Backlog",
                    "Jira Tasks",
                    "Product Roadmap",
                    "Executive Summary"
                ],
                key="cfg_deliverable"
            )
        with col5:
            detail_level = st.selectbox(
                "Detail Level",
                options=["Basic", "Standard", "Comprehensive"],
                index=1,
                key="cfg_detail_level"
            )
        with col6:
            st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)
            include_risk = st.checkbox("Include Risk Analysis", value=True, key="cfg_risk")
            
    return industry, product_type, audience, deliverable, detail_level, include_risk

