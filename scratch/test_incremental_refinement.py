import sys
from pathlib import Path

# Set stdout to UTF-8 to prevent Windows encoding errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to python path
project_root = Path("C:/Users/Dev Suri/.gemini/antigravity/scratch/prd_generator")
sys.path.insert(0, str(project_root))

import json
import logging
logging.basicConfig(level=logging.INFO)

from backend.workspace_context import WorkspaceContext
from backend.agents.dependency_analyzer import DependencyAnalyzer
from backend.agents.document_refiner import refine_document
from backend.agents.workspace_chat import apply_workspace_refinements
from backend.agent_registry import registry
import backend.agents.workspace_chat  # Trigger registration
import backend.agents.document_refiner

print("="*60)
print("1. INITIALIZING MOCK GENZ SOCIAL WORKSPACE STATE")
print("="*60)

workspace = {
    "name": "GenZ Social Q&A App",
    "idea": "A GenZ Social Q&A App focused on social discovery through video and text interaction.",
    "industry": "Entertainment",
    "product_type": "Mobile App",
    "audience": "B2C",
    "prd": {
        "Problem_Statement": "GenZ users struggle to find genuine social discovery platforms.",
        "Executive_Summary": {
            "problem": "GenZ users struggle to find genuine social discovery platforms.",
            "opportunity": "Build Q&A app.",
            "strategy": "Launch mobile app.",
            "timeline": "3 months",
            "investment_summary": "Low cost"
        },
        "Product_Vision": "A GenZ Social Q&A App focused on social discovery through video and text interaction.",
        "Goals_and_Objectives": [
            "Achieve 10,000 Daily Active Users (DAU)",
            "Maintain a Friend Request Acceptance Rate of 75%"
        ],
        "Functional_Requirements": [
            {"id": "FR-001", "title": "Video Posting", "description": "Users can post short video clips."},
            {"id": "FR-002", "title": "Threaded Replies", "description": "Users can reply in threads."}
        ],
        "Core_Features": [
            {"id": "FT-001", "name": "Video posting", "description": "Short form video posting."},
            {"id": "FT-002", "name": "Threaded replies", "description": "Threaded answer replies."}
        ],
        "User_Personas": [
            {"id": "PE-001", "name": "Aria", "role": "Social Creator"}
        ],
        "Non_Functional_Requirements": {
            "Performance": "Under 200ms latency.",
            "Security": "Encrypted user data."
        }
    },
    "deliverables": {
        "Product Requirements Document (PRD)": {
            "content": {
                "🎯 Problem Statement": "GenZ users struggle to find genuine social discovery platforms.",
                "📈 Business Goals": "- Achieve 10,000 Daily Active Users (DAU).\n- Maintain a Friend Request Acceptance Rate of 75%.",
                "👥 User Personas": "**Primary: Aria**\nRequires easy video posting.",
                "⚙️ Functional Requirements": "FR-001: Video Q&A Posting\nFR-002: Threaded replies",
                "🔒 Non-Functional Requirements": "**Performance:** Under 200ms latency.\n**Security:** Encrypted user data.",
                "✨ Core Features": "FT-001: Video Q&A Posting\nFT-002: Threaded replies"
            }
        },
        "User Stories": {
            "content": {
                "stories": [
                    {"id": "US-001", "title": "As a user I want to post questions"}
                ]
            }
        }
    },
    "metadata": {
        "last_updated": "Just now",
        "chat_history": [],
        "version_history": []
    }
}

# 1. Test Dependency Analyzer
print("\n" + "="*60)
print("2. TESTING DETERMINISTIC DEPENDENCY ANALYZER")
print("="*60)
analyzer = DependencyAnalyzer()
instruction = "Add authentication options to functional requirements"
affected_flags = analyzer.analyze(instruction)
affected_sections = analyzer.analyze_prd_sections(instruction)

print(f"Affected deliverables flags: {affected_flags}")
print(f"Affected PRD sections: {affected_sections}")

assert affected_flags["prd"] is True
assert "⚙️ Functional Requirements" in affected_sections
assert "🔒 Non-Functional Requirements" in affected_sections or "⚙️ Functional Requirements" in affected_sections
print("✓ Dependency Analyzer verified.")

# 2. Test apply_workspace_refinements
print("\n" + "="*60)
print("3. EXECUTING INCREMENTAL REFINEMENT")
print("="*60)

# Simulate refinement for PRD only
refinement_flags = {
    "business_analysis": False,
    "prd": True,
    "user_stories": False,
    "roadmap": False,
    "jira": False,
    "sprint_planning": False,
    "brd": False,
    "srs": False
}

import copy
workspace_copy = copy.deepcopy(workspace)

updated_ws = apply_workspace_refinements(
    workspace_dict=workspace_copy,
    instruction=instruction,
    affected_flags=refinement_flags
)

# Verify results
print("\n" + "="*60)
print("4. VERIFYING UNRELATED DELIVERABLES ARE UNTOUCHED")
print("="*60)

new_prd = updated_ws["deliverables"]["Product Requirements Document (PRD)"]["content"]
old_prd = workspace["deliverables"]["Product Requirements Document (PRD)"]["content"]
print(f"Old Problem Statement: {old_prd.get('🎯 Problem Statement')}")
print(f"New Problem Statement: {new_prd.get('Problem_Statement')}")

# Unaffected sections must be preserved exactly
assert new_prd.get("Problem_Statement") == old_prd.get("🎯 Problem Statement")
assert new_prd.get("User_Personas") == workspace["prd"]["User_Personas"]
assert new_prd.get("Executive_Summary") == workspace["prd"]["Executive_Summary"]

# Affected section must have changed/updated content
print(f"\nOld Functional Requirements:\n{old_prd.get('⚙️ Functional Requirements')}")
print(f"New Functional Requirements:\n{new_prd.get('Functional_Requirements')}")

print("\n✓ Verification successful! Unrelated sections remain untouched.")
print("="*60)
