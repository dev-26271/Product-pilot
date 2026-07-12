import logging
import json
from backend.agents.business_analyst import generate_business_analysis
from backend.agents.product_manager import generate_product_requirements

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main() -> None:
    """Runs a local verification of the complete multi-agent pipeline (BA + PM)."""
    user_input = {
        "idea": "Build a healthcare platform where patients can consult doctors online, manage prescriptions, schedule appointments, and receive AI-powered health recommendations.",
        "industry": "Healthcare",
        "product_type": "Mobile Application",
        "audience": "B2C"
    }
    
    print("\n[Test Agent Pipeline] Step 1: Triggering Business Analyst Agent...")
    try:
        business_analysis = generate_business_analysis(user_input)
        print("\n[Test Agent Pipeline] Business Analysis generated successfully:")
        print(json.dumps(business_analysis, indent=2))
        
        print("\n[Test Agent Pipeline] Step 2: Triggering Product Manager Agent...")
        product_requirements = generate_product_requirements(business_analysis)
        print("\n[Test Agent Pipeline] Product Requirements generated successfully:")
        print(json.dumps(product_requirements, indent=2))
        
    except Exception as e:
        print(f"\n[Test Agent Pipeline] Execution failed with error: {e}")

if __name__ == "__main__":
    main()
