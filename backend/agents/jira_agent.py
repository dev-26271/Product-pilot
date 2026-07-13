import json
from typing import Dict, Any, List
from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.prompts import JIRA_AGENT_SYSTEM_PROMPT

class JiraAgent(BaseDocumentAgent):
    """Jira Agent that generates Jira Tasks based on PRD and User Stories."""
    
    @property
    def required_inputs(self) -> List[str]:
        return ["prd"]
        
    @property
    def output_schema_keys(self) -> List[str]:
        return ["🎫 Jira Tasks"]
        
    @property
    def system_prompt(self) -> str:
        return JIRA_AGENT_SYSTEM_PROMPT
        
    @property
    def agent_name(self) -> str:
        return "JiraAgent"
        
    @property
    def deliverable_key(self) -> str:
        return "Jira Tasks"

    def build_user_message(self, context: WorkspaceContext) -> str:
        base_msg = super().build_user_message(context)
        
        raw_us = context.deliverables.get("User Stories", {})
        if isinstance(raw_us, dict) and "stories" in raw_us:
            user_stories_context = raw_us.get("stories", [])
        elif isinstance(raw_us, dict) and "content" in raw_us:
            user_stories_context = raw_us["content"]
        else:
            user_stories_context = []
            
        extra_msg = f"""
=== USER STORIES ===
{json.dumps(user_stories_context, indent=2) if user_stories_context else "Not generated yet. Base tasks on the PRD only."}
"""
        return base_msg + "\n" + extra_msg

# Auto-register agent
registry.register("jira", JiraAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_jira_tasks(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("jira").execute(workspace)
        return result_context.deliverables["Jira Tasks"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("jira").execute(ctx)
        return result_context.deliverables["Jira Tasks"]["content"]
