import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.agents.entity_schema import (
    validate_entity_envelope, validate_domain_fields, ROADMAP_PHASE_REQUIRED
)
from backend.prompts import ROADMAP_AGENT_SYSTEM_PROMPT

import logging
logger = logging.getLogger(__name__)


class RoadmapAgent(BaseDocumentAgent):
    """Roadmap Agent — produces canonical structured Roadmap Phase entities."""

    @property
    def required_inputs(self) -> List[str]:
        return ["prd"]

    @property
    def output_schema_keys(self) -> List[str]:
        # New canonical schema uses 'phases'; legacy fallback also accepted
        return []

    @property
    def system_prompt(self) -> str:
        return ROADMAP_AGENT_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "RoadmapAgent"

    @property
    def deliverable_key(self) -> str:
        return "Product Roadmap"

    def build_user_message(self, context: WorkspaceContext) -> str:
        base_msg = super().build_user_message(context)
        raw_us = context.deliverables.get("User Stories", {})
        us_epics = raw_us.get("epics", []) if isinstance(raw_us, dict) else []
        extra_msg = f"""
=== USER STORY EPICS ===
{json.dumps(us_epics, indent=2) if us_epics else "Not generated yet. Build roadmap from the PRD only."}

Current UTC timestamp: {datetime.now(timezone.utc).isoformat()}
"""
        return base_msg + "\n" + extra_msg

    def post_processing(self, parsed_json: Dict[str, Any], context: WorkspaceContext) -> WorkspaceContext:
        """Validate entities and format phases into markdown for the UI."""
        phases = parsed_json.get("phases", [])

        # Handle legacy string-blob output from old prompt
        if not phases:
            legacy_text = (
                parsed_json.get("\U0001f5d3\ufe0f Product Roadmap")
                or parsed_json.get("Product Roadmap", "")
            )
            if legacy_text:
                logger.warning("RoadmapAgent: received legacy string output; wrapping in a single phase entity.")
                phases = [{
                    "id": "SP-001", "phase": "MVP", "quarter": "Q3 2026",
                    "objectives": [legacy_text[:200]],
                    "milestones": [], "dependencies": [], "success_metrics": [],
                    "release_risks": [], "go_no_go_criteria": [],
                    "version": "1.0", "status": "Planned",
                    "confidence": 0.70, "priority_score": 9, "risk_score": 5,
                    "ownership": {"agent": "RoadmapAgent", "created_at": datetime.now(timezone.utc).isoformat(), "last_modified_by": "RoadmapAgent"},
                    "source_attribution": [], "traceability": {}, "relationships": [],
                }]

        # Validate entities
        all_warnings = []
        for phase in phases:
            all_warnings.extend(validate_entity_envelope(phase, phase.get("id", "SP-?")))
            all_warnings.extend(validate_domain_fields(phase, ROADMAP_PHASE_REQUIRED, phase.get("id", "SP-?")))
        if all_warnings:
            logger.warning(f"RoadmapAgent: {len(all_warnings)} entity warnings:\n" + "\n".join(f"  \u26a0 {w}" for w in all_warnings))

        # Format phases into markdown for UI delivery
        roadmap_md = _format_phases_as_markdown(phases)

        # Store both: raw canonical entities AND rendered markdown
        new_deliverables = context.deliverables.copy()
        new_deliverables[self.deliverable_key] = {
            "content": {"\U0001f5d3\ufe0f Product Roadmap": roadmap_md},
            "entities": {"phases": phases},
        }
        return context.clone(deliverables=new_deliverables)


def _format_phases_as_markdown(phases: List[Dict[str, Any]]) -> str:
    parts = []
    for ph in phases:
        phase_name = ph.get("phase", "Phase")
        quarter = ph.get("quarter", "")
        objs = ph.get("objectives", [])
        objs_str = "\n".join(f"  - {o}" for o in objs) if isinstance(objs, list) else str(objs)
        milestones = ph.get("milestones", [])
        miles_str = "\n".join(
            f"  - {m['date']}: {m['description']}" if isinstance(m, dict) else f"  - {m}"
            for m in milestones
        )
        deps = ph.get("dependencies", [])
        deps_str = ", ".join(deps) if isinstance(deps, list) else str(deps)
        metrics = ph.get("success_metrics", [])
        metrics_str = "\n".join(f"  - {m}" for m in metrics) if isinstance(metrics, list) else str(metrics)
        risks = ph.get("release_risks", [])
        risks_str = "\n".join(f"  - {r}" for r in risks) if isinstance(risks, list) else str(risks)
        gngo = ph.get("go_no_go_criteria", [])
        gngo_str = "\n".join(f"  - {c}" for c in gngo) if isinstance(gngo, list) else str(gngo)
        confidence = ph.get("confidence", "")
        phase_id = ph.get("id", "SP-?")

        parts.append(
            f"### {phase_id} \u2014 {phase_name} ({quarter})\n\n"
            f"**Objectives:**\n{objs_str}\n\n"
            f"**Milestones:**\n{miles_str or '  - TBD'}\n\n"
            f"**Dependencies:** {deps_str or 'None'}\n\n"
            f"**Success Metrics:**\n{metrics_str or '  - TBD'}\n\n"
            f"**Release Risks:**\n{risks_str or '  - None identified'}\n\n"
            f"**Go/No-Go Criteria:**\n{gngo_str or '  - TBD'}\n\n"
            f"*Confidence: {confidence} | Risk Score: {ph.get('risk_score', '?')}/10*"
        )
    return "\n\n---\n\n".join(parts)


# Auto-register agent
registry.register("roadmap", RoadmapAgent())


# -- Backwards Compatible Public Wrapper --
def generate_roadmap(workspace: Any) -> Dict[str, Any]:
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("roadmap").execute(workspace)
        return result_context.deliverables["Product Roadmap"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("roadmap").execute(ctx)
        return result_context.deliverables["Product Roadmap"]["content"]
