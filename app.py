import streamlit as st
from ui.styles import load_custom_css
from ui.sidebar import render_sidebar
from ui.home import render_home

# Configure page to wide layout for the enterprise workspace width
st.set_page_config(
    page_title="ProductPilot Workspace",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Pre-populate Mock Project Database to simulate a persistent product workspace
if 'projects' not in st.session_state:
    st.session_state['projects'] = {
        "Healthcare AI": {
            "name": "Healthcare AI",
            "metadata": "Updated 2h ago",
            "idea": "Build a healthcare platform where patients can consult doctors online, manage prescriptions, schedule appointments, and receive AI-powered health recommendations.",
            "industry": "Healthcare",
            "product_type": "Mobile Application",
            "audience": "B2C",
            "deliverables": {
                "Product Requirements Document (PRD)": {
                    "content": {
                        "🎯 Problem Statement": "Patients with chronic conditions like diabetes lack real-time continuous feedback from clinical teams, causing delayed response rates during glycemic events.",
                        "📈 Business Goals": "- Reduce critical diabetic response intervals by 65% within initial testing.\n- Establish active connections with 1,000+ board-certified physicians in the first cycle.\n- Achieve patient satisfaction score (CSAT) of 92% or higher.",
                        "👥 User Personas": "**Primary: Dr. Sarah**\nRequires clean telemetry history visualizers and automated threshold event logging.\n\n**Secondary: Patient David**\nRequires a lightweight mobile telemetry reporter syncing securely with passive wearable APIs.",
                        "✨ Features": "1. **Wearable Telemetry Sync:** Continuous glucose data integration API.\n2. **Emergency Threshold Trigger:** Direct notification relays to clinical coordinators.\n3. **Clinical Intakes Portal:** Consolidated telemetry reports with export capabilities."
                    }
                },
                "User Stories": {
                    "content": {
                        "📖 Patient Stories": "- *As a patient, I want my glucose levels to sync automatically so I don't have to enter them manually.*\n- *As a patient, I want an alert when my glucose levels are dangerously high so I can take immediate action.*",
                        "📖 Doctor Stories": "- *As a doctor, I want to see a patient's historical trends in a single dashboard so I can make informed adjustments to their plan.*"
                    }
                },
                "Product Roadmap": {
                    "content": {
                        "🗓️ Phase 1 (Q3 2026)": "- Core Telemetry API Integration\n- Patient iOS/Android App Launch (Beta)\n- Direct Messaging Service",
                        "🗓️ Phase 2 (Q4 2026)": "- Hospital EHR System Integration (HL7/FHIR)\n- Predictive Risk Analytics Dashboard"
                    }
                }
            }
        },
        "Food Delivery Platform": {
            "name": "Food Delivery Platform",
            "metadata": "Updated 1d ago",
            "idea": "A hyper-local food delivery marketplace optimized for eco-friendly drone shipping and zero-waste packaging.",
            "industry": "Retail",
            "product_type": "Marketplace",
            "audience": "B2C",
            "deliverables": {
                "Executive Summary": {
                    "content": {
                        "🎯 Vision": "Establish the world's first carbon-neutral, hyper-local food logistics framework using automated drone delivery nodes.",
                        "📈 Market Opportunity": "Demand for green delivery options has surged by 180% year-over-year in metropolitan test areas."
                    }
                }
            }
        },
        "CRM SaaS": {
            "name": "CRM SaaS",
            "metadata": "Draft",
            "idea": "A privacy-first CRM SaaS designed for security-conscious enterprise teams with local-first syncing and end-to-end encryption.",
            "industry": "Finance",
            "product_type": "SaaS Platform",
            "audience": "Enterprise",
            "deliverables": {}
        },
        "Student Assistant": {
            "name": "Student Assistant",
            "metadata": "Draft",
            "idea": "An offline-first study companion utilizing localized LLMs for private research, summarizing, and flashcard generation.",
            "industry": "Education",
            "product_type": "Productivity Tool",
            "audience": "B2B",
            "deliverables": {}
        }
    }
    st.session_state['active_project_id'] = None # "New Project" mode by default

# Track canvas text in session state to allow chip-fill interaction
if 'idea_input' not in st.session_state:
    st.session_state['idea_input'] = ""

def main():
    load_custom_css()
    render_sidebar()
    
    # Check sidebar view selection to toggle between views
    view_mode = st.session_state.get("nav_page_selection", "Workspace")
    if view_mode == "RAG Inspector":
        from ui.output import render_rag_inspector
        render_rag_inspector()
    elif view_mode == "Dashboard":
        from ui.output import render_workspace_dashboard
        render_workspace_dashboard()
    elif view_mode == "Traceability Explorer":
        from ui.output import render_traceability_explorer
        render_traceability_explorer()
    else:
        render_home()

if __name__ == "__main__":
    main()
