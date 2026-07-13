import json
from typing import Dict, Any, List
from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.prompts import SPRINT_PLANNING_AGENT_SYSTEM_PROMPT

class SprintPlanningAgent(BaseDocumentAgent):
    """Sprint Planning Agent that generates the Sprint Backlog from PRD and User Stories."""
    
    @property
    def required_inputs(self) -> List[str]:
        return ["prd"]
        
    @property
    def output_schema_keys(self) -> List[str]:
        return ["🏃 Sprint Backlog"]
        
    @property
    def system_prompt(self) -> str:
        return SPRINT_PLANNING_AGENT_SYSTEM_PROMPT
        
    @property
    def agent_name(self) -> str:
        return "SprintPlanningAgent"
        
    @property
    def deliverable_key(self) -> str:
        return "Sprint Backlog"

    def build_user_message(self, context: WorkspaceContext) -> str:
        base_msg = super().build_user_message(context)
        
        raw_us = context.deliverables.get("User Stories", {})
        if isinstance(raw_us, dict) and "stories" in raw_us:
            us_epics   = raw_us.get("epics", [])
            us_stories = raw_us.get("stories", [])
            user_stories_context = {"epics": us_epics, "stories": us_stories}
        elif isinstance(raw_us, dict) and "content" in raw_us:
            user_stories_context = raw_us["content"]
        else:
            user_stories_context = {}
            
        extra_msg = f"""
=== USER STORIES AND EPICS ===
{json.dumps(user_stories_context, indent=2) if user_stories_context else "Not generated yet. Base sprint backlog on the PRD only."}
"""
        return base_msg + "\n" + extra_msg

# Auto-register agent
registry.register("sprint_planning", SprintPlanningAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_sprint_backlog(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("sprint_planning").execute(workspace)
        return result_context.deliverables["Sprint Backlog"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("sprint_planning").execute(ctx)
        return result_context.deliverables["Sprint Backlog"]["content"]
