import logging
import json
from backend.agents import generate_business_analysis

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main() -> None:
    """Runs a local verification of the Business Analyst agent execution."""
    user_input = {
        "idea": "Build a healthcare platform where patients can consult doctors online, manage prescriptions, schedule appointments, and receive AI-powered health recommendations.",
        "industry": "Healthcare",
        "product_type": "Mobile Application",
        "audience": "B2C"
    }
    
    print("\n[Test Agent] Triggering Business Analyst Agent with mock payload...")
    try:
        analysis = generate_business_analysis(user_input)
        print("\n[Test Agent] Business Analysis generated successfully:")
        print(json.dumps(analysis, indent=2))
    except Exception as e:
        print(f"\n[Test Agent] Generation failed with error: {e}")

if __name__ == "__main__":
    main()
