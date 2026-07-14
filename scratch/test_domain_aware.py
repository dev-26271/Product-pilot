import os
import sys

# Add root project path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.workspace_context import WorkspaceContext
from backend.domains import detect_domain
from backend.agents.business_analyst import BusinessAnalystAgent
from backend.agents.product_manager import ProductManagerAgent
from backend.validation.validator import DeterministicValidator

def main():
    print("=========================================================")
    print("TESTING DOMAIN DETECTION STRATEGY")
    print("=========================================================")
    
    towel_idea = "A premium bamboo bath towel brand focusing on quick-drying and anti-odor features for luxury hotels."
    saas_idea = "A collaborative workspace SaaS for remote product management teams with document synchronization and task trackers."
    ai_idea = "An autonomous AI coding assistant that edits codebase files and runs terminal commands to fix linting errors."
    marketplace_idea = "A marketplace where independent drone operators sell mapping services to real estate developers."

    assert detect_domain(towel_idea) == "Physical Consumer Product"
    assert detect_domain(saas_idea) == "SaaS Platform"
    assert detect_domain(ai_idea) == "AI Product / AI Platform"
    assert detect_domain(marketplace_idea) == "Marketplace"
    
    print("Domain detection strategy matches all test cases.")
    
    # Test Towel Generation
    print("\n=========================================================")
    print("TESTING GENERATION & VALIDATION FOR BAMBOO TOWEL")
    print("=========================================================")
    ctx = WorkspaceContext(idea=towel_idea)
    ctx.intent_context = {
        "project_name": "Towel Brand",
        "industry": {"value": "Retail"},
        "product_type": {"value": "Physical Consumer Product"},
        "audience": {"value": "B2B"},
        "problem_statement": "Luxury hotels suffer from high laundry energy bills and towel odors.",
        "core_features": ["Quick-dry fabric weaves", "Natural anti-odor compounds"]
    }
    
    ba_agent = BusinessAnalystAgent()
    pm_agent = ProductManagerAgent()
    validator = DeterministicValidator()
    
    print("1. Running Business Analyst...")
    ctx = ba_agent.execute(ctx)
    print("   User Personas generated:", [p["name"] for p in ctx.business_analysis.get("user_personas", [])])
    
    print("2. Running Product Manager...")
    ctx = pm_agent.execute(ctx)
    print("   PRD top-level keys generated:", list(ctx.prd.keys()))
    
    # Check that extra sections are present in formatted deliverables
    content = ctx.deliverables["Product Requirements Document (PRD)"]["content"]
    print("   Formatted section titles:")
    for k in content.keys():
        clean_k = k.encode("ascii", errors="ignore").decode("ascii").strip()
        print(f"     - {clean_k}")
        
    assert any("Materials" in k for k in content.keys())
    assert any("Manufacturing" in k for k in content.keys())
    assert any("Packaging" in k for k in content.keys())
    
    print("3. Running Deterministic Validation...")
    val_report = validator.validate(ctx)
    print("   Validation result:", val_report["valid"])
    print("   Validation score:", val_report["score"])
    print("   Validation errors:", val_report["errors"])
    print("   Validation warnings:", val_report["warnings"])
    
    # Verify that the new domain integrity rules are active and pass
    domain_errors = [e for e in val_report["errors"] if "Physical Product contains" in e or "Software product contains" in e]
    print("   Domain integrity errors (should be 0):", len(domain_errors))
    assert len(domain_errors) == 0
    
    print("\n=========================================================")
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=========================================================")

if __name__ == "__main__":
    main()
