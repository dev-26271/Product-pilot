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
