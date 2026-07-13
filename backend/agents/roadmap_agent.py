import json
from typing import Dict, Any, List
from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.prompts import ROADMAP_AGENT_SYSTEM_PROMPT

class RoadmapAgent(BaseDocumentAgent):
    """Roadmap Agent that generates the Product Roadmap based on PRD and Epics."""
    
    @property
    def required_inputs(self) -> List[str]:
        return ["prd"]
        
    @property
    def output_schema_keys(self) -> List[str]:
        return ["🗓️ Product Roadmap"]
        
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
        if isinstance(raw_us, dict) and "epics" in raw_us:
            us_epics_context = raw_us.get("epics", [])
        else:
            us_epics_context = []
            
        extra_msg = f"""
=== USER STORY EPICS ===
{json.dumps(us_epics_context, indent=2) if us_epics_context else "Not generated yet. Build roadmap from the PRD only."}
"""
        return base_msg + "\n" + extra_msg

# Auto-register agent
registry.register("roadmap", RoadmapAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_roadmap(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("roadmap").execute(workspace)
        return result_context.deliverables["Product Roadmap"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("roadmap").execute(ctx)
        return result_context.deliverables["Product Roadmap"]["content"]
