import logging
import json
from backend.agents.brd_agent import generate_brd
from backend.agents.document_refiner import refine_document

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main() -> None:
    """Verifies compilation and refinement of individual specialized agent documents."""
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
                    "👥 User Personas": "**Rachel (Patient)**\nNeeds simple scheduling interface."
                }
            }
        }
    }
    
    print("\n[Test Lazy Agent] Step 1: Triggering BRD Agent for lazy document generation...")
    try:
        brd_content = generate_brd(mock_workspace)
        print("\n[Test Lazy Agent] BRD generated successfully:")
        print(json.dumps(brd_content, indent=2))
        
        # Test refinement
        print("\n[Test Lazy Agent] Step 2: Triggering Document Refiner to modify the generated BRD...")
        instruction = "Add compliance with HIPAA logs to compliance section."
        refined_brd = refine_document(
            document_name="Business Requirements Document (BRD)",
            current_content=brd_content,
            instruction=instruction,
            workspace=mock_workspace
        )
        print("\n[Test Lazy Agent] Refined BRD content:")
        print(json.dumps(refined_brd, indent=2))
        
    except Exception as e:
        print(f"\n[Test Lazy Agent] Execution failed with error: {e}")

if __name__ == "__main__":
    main()
