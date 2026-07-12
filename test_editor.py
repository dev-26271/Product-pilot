import logging
import json
from backend.agents.workspace_editor import update_workspace

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main() -> None:
    """Runs a local verification of the Workspace Editor agent."""
    mock_workspace = {
        "name": "Healthcare Project",
        "idea": "Build a healthcare platform where patients can consult doctors online, manage prescriptions, schedule appointments.",
        "industry": "Healthcare",
        "product_type": "Mobile Application",
        "audience": "B2C",
        "deliverables": {
            "Product Requirements Document (PRD)": {
                "content": {
                    "🎯 Problem Statement": "Patients face issues booking and tracking visits.",
                    "📈 Business Goals": "- Reduce wait times by 30%\n- Support 500 bookings monthly",
                    "👥 User Personas": "**Rachel (Patient)**\nNeeds simple scheduling interface.",
                    "✨ Features": "**Booking System (High)**\nInteractive booking calendar.",
                    "🗓️ Product Roadmap": "**Phase 1**\nCalendar integration."
                }
            }
        }
    }
    
    instruction = "Add a feature for push notification alerts for scheduled doctor visits, and ensure it is prioritized as High in Phase 1."
    
    print("\n[Test Workspace Editor] Triggering workspace editor agent with instruction...")
    try:
        updated = update_workspace(mock_workspace, instruction)
        print("\n[Test Workspace Editor] Workspace updated successfully:")
        print(json.dumps(updated, indent=2))
    except Exception as e:
        print(f"\n[Test Workspace Editor] Refinement failed with error: {e}")

if __name__ == "__main__":
    main()
