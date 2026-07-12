import logging
import json
from backend.agents.workspace_chat import chat_refine_workspace

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main() -> None:
    """Runs a local verification of the PM chat refinement agent."""
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
    
    chat_history = [
        {"role": "assistant", "content": "Hello, I am your senior Product Manager. How can I help refine this project today?"}
    ]
    
    user_message = "Add a feature for push notification alerts for scheduled doctor visits, and ensure it is prioritized as High in Phase 1."
    
    print("\n[Test Chat] Triggering PM chat refinement...")
    try:
        result = chat_refine_workspace(mock_workspace, chat_history, user_message)
        print("\n[Test Chat] Refinement generated successfully:")
        print(f"Chat Response: {result.get('chat_response')}")
        print(f"Updated Tabs: {result.get('updated_tabs')}")
        print("Updated Deliverables JSON:")
        print(json.dumps(result.get('deliverables'), indent=2))
    except Exception as e:
        print(f"\n[Test Chat] Refinement failed with error: {e}")

if __name__ == "__main__":
    main()
