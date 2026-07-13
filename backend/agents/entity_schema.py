"""
entity_schema.py -- Canonical Entity Envelope for ProductPilot v2

Every generated object (Business Goal, Persona, Feature, FR, User Story,
Roadmap Phase, Jira Task) must conform to the canonical envelope defined here.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


CANONICAL_ENVELOPE_FIELDS = (
    "id", "version", "status", "confidence",
    "priority_score", "risk_score", "ownership",
    "source_attribution", "traceability", "relationships",
)

VALID_STATUSES = {"Draft","Active","Planned","In Progress","Done","Deprecated","To Do","Blocked","Ready"}
VALID_PRIORITIES_TEXT = {"Critical", "High", "Medium", "Low"}
VALID_TASK_TYPES = {"Frontend","Backend","Database","API","Testing","DevOps","Documentation"}
FIBONACCI_POINTS = {1, 2, 3, 5, 8, 13}


def build_envelope(
    entity_id: str,
    agent_name: str,
    confidence: float = 0.90,
    priority_score: int = 5,
    risk_score: int = 3,
    status: str = "Draft",
    version: str = "1.0",
    source_attribution: Optional[List[str]] = None,
    traceability: Optional[Dict[str, Any]] = None,
    relationships: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Returns the canonical envelope fields for any entity."""
    return {
        "id": entity_id,
        "version": version,
        "status": status,
        "confidence": round(float(confidence), 2),
        "priority_score": int(priority_score),
        "risk_score": int(risk_score),
        "ownership": {
            "agent": agent_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_modified_by": agent_name,
        },
        "source_attribution": source_attribution or [],
        "traceability": traceability or {},
        "relationships": relationships or [],
    }


def validate_entity_envelope(entity: Dict[str, Any], entity_label: str = "") -> List[str]:
    """Validates that the entity carries all required canonical envelope fields."""
    violations: List[str] = []
    label = entity_label or entity.get("id", "<unknown>")

    for field in CANONICAL_ENVELOPE_FIELDS:
        if field not in entity:
            violations.append(f"{label}: missing canonical field '{field}'")

    if "confidence" in entity:
        c = entity["confidence"]
        if not isinstance(c, (int, float)) or not (0.0 <= float(c) <= 1.0):
            violations.append(f"{label}: confidence must be float in [0,1], got {c!r}")

    for sf in ("priority_score", "risk_score"):
        if sf in entity:
            v = entity[sf]
            if not isinstance(v, int) or not (1 <= v <= 10):
                violations.append(f"{label}: {sf} must be int in [1,10], got {v!r}")

    if "ownership" in entity:
        own = entity["ownership"]
        if not isinstance(own, dict) or "agent" not in own or "created_at" not in own:
            violations.append(f"{label}: ownership must have agent and created_at")

    if "relationships" in entity:
        rels = entity["relationships"]
        if not isinstance(rels, list):
            violations.append(f"{label}: relationships must be array")
        else:
            for i, rel in enumerate(rels):
                if not isinstance(rel, dict) or "type" not in rel or "target_id" not in rel:
                    violations.append(f"{label}: relationship[{i}] needs type and target_id")

    return violations


BUSINESS_GOAL_REQUIRED = {
    "id","goal","smart","owner","kpi","baseline","target_value","timeline",
}
PERSONA_REQUIRED = {
    "id","name","role","goals","frustrations","workflow","technical_proficiency","motivations",
}
FEATURE_REQUIRED = {
    "id","name","description","business_value","functional_requirement_ids",
    "user_persona","acceptance_criteria","success_metrics","kpis",
    "dependencies","risks","assumptions","edge_cases",
}
FUNCTIONAL_REQUIREMENT_REQUIRED = {
    "id","title","description","business_value","user_persona",
    "acceptance_criteria","success_metrics","kpis",
    "dependencies","risks","assumptions","edge_cases",
    "non_functional_requirements","priority",
}
USER_STORY_REQUIRED = {
    "id","epic_id","feature","title","persona",
    "as_a","i_want","so_that",
    "acceptance_criteria","definition_of_done",
    "priority","estimate","dependencies","risk","status",
    "traceability","labels",
}
ROADMAP_PHASE_REQUIRED = {
    "id","phase","quarter","objectives","milestones",
    "dependencies","success_metrics","release_risks","go_no_go_criteria",
}
JIRA_TASK_REQUIRED = {
    "id","type","title","description","estimate",
    "priority","acceptance_criteria","dependencies","labels","status","traceability",
}


def validate_domain_fields(
    entity: Dict[str, Any],
    required_fields: set,
    entity_label: str = "",
) -> List[str]:
    """Checks a domain entity carries all required domain-specific fields."""
    label = entity_label or entity.get("id", "<unknown>")
    return [
        f"{label}: missing domain field '{f}'"
        for f in required_fields
        if f not in entity or entity[f] in (None, "", [], {})
    ]


def calculate_planning_analysis(context: Any) -> Dict[str, Any]:
    """Calculates workspace dashboard planning metrics and recommendations deterministically in Python."""
    # 1. Maturity Scores
    idea_val = 1.0
    
    ba = context.business_analysis or {}
    has_goals = len(ba.get("business_goals", [])) > 0
    has_personas = len(ba.get("user_personas", [])) > 0
    if has_goals and has_personas:
        business_val = 1.0
    elif has_goals or has_personas:
        business_val = 0.6
    else:
        business_val = 0.0
        
    prd = context.prd or {}
    has_features = len(prd.get("features", [])) > 0 or len(prd.get("core_features", [])) > 0
    has_reqs = len(prd.get("functional_requirements", [])) > 0 or len(prd.get("requirements", [])) > 0
    if has_features and has_reqs:
        requirements_val = 1.0
    elif has_features or has_reqs:
        requirements_val = 0.6
    else:
        requirements_val = 0.0
        
    has_roadmap = "Product Roadmap" in context.deliverables
    has_srs = "Software Requirements Specification (SRS)" in context.deliverables
    if has_roadmap and has_srs:
        architecture_val = 1.0
    elif has_roadmap or has_srs:
        architecture_val = 0.6
    else:
        architecture_val = 0.0
        
    has_stories = "User Stories" in context.deliverables
    has_jira = "Jira Tasks" in context.deliverables
    if has_stories and has_jira:
        testing_val = 1.0
    elif has_stories or has_jira:
        testing_val = 0.6
    else:
        testing_val = 0.0

    validation_report = context.metadata.get("validation_report", {})
    val_score = validation_report.get("score", 1.0)
    
    business_val = round(business_val * val_score, 2)
    requirements_val = round(requirements_val * val_score, 2)
    
    maturity_scores = {
        "idea": idea_val,
        "business": business_val,
        "requirements": requirements_val,
        "architecture": architecture_val,
        "testing": testing_val
    }

    # 2. Recommended Actions
    recommended_actions = []
    if not context.business_analysis:
        recommended_actions.extend([
            "Define target audience & business goals",
            "Generate user personas"
        ])
    if not context.prd:
        recommended_actions.append("Generate Product Requirements Document (PRD)")
    if "User Stories" not in context.deliverables:
        recommended_actions.append("Generate detailed User Stories and Acceptance Criteria")
    if "Product Roadmap" not in context.deliverables:
        recommended_actions.append("Create strategic Product Roadmap phases")
    if "Jira Tasks" not in context.deliverables:
        recommended_actions.append("Generate developer Jira Tasks with story points")
    if "Sprint Backlog" not in context.deliverables:
        recommended_actions.append("Construct Sprint Backlog and backlog allocation")
        
    errors = validation_report.get("errors", [])
    warnings = validation_report.get("warnings", [])
    if errors or warnings:
        recommended_actions.append("Resolve open validation audits & traceability gaps")
        
    if not recommended_actions:
        recommended_actions = [
            "Conduct requirements feedback session with key stakeholders",
            "Perform sprint planning dry run and backlog refinement",
            "Run automated QA test generation"
        ]

    # 3. Smart Recommendations
    smart_recommendations = []
    for warn in warnings[:4]:
        text = str(warn)
        rec_type = "Requirements Gap"
        if "traceability" in text.lower():
            rec_type = "Traceability Gap"
        elif "missing" in text.lower():
            rec_type = "Missing Attribute"
        elif "fibonacci" in text.lower() or "points" in text.lower():
            rec_type = "Estimation Warning"
        smart_recommendations.append({
            "type": rec_type,
            "description": text
        })
        
    if len(smart_recommendations) < 3:
        if not context.business_analysis:
            smart_recommendations.append({
                "type": "Target KPI Alignment",
                "description": "Establish baseline and target values for the MVP time-bound goals."
            })
        if not context.prd:
            smart_recommendations.append({
                "type": "Success Criteria",
                "description": "Map product features back to quantitative user performance goals."
            })
        if "User Stories" not in context.deliverables:
            smart_recommendations.append({
                "type": "Acceptance Criteria",
                "description": "Ensure Definition of Done (DoD) is clearly defined for all prospective epics."
            })
        if "Product Roadmap" not in context.deliverables:
            smart_recommendations.append({
                "type": "Phase Dependency",
                "description": "Determine critical path and external dependencies between release milestones."
            })
        smart_recommendations.append({
            "type": "Metric Refinement",
            "description": "Define engineering indicators to track actual features utilization post-launch."
        })
        smart_recommendations.append({
            "type": "Traceability",
            "description": "Map all functional requirements back to target business goals to prevent scope creep."
        })
        
    return {
        "maturity_scores": maturity_scores,
        "recommended_actions": recommended_actions[:5],
        "smart_recommendations": smart_recommendations[:4]
    }
