import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import JIRA_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class JiraAgent(BaseAgent):
    """Jira Agent that generates Jira Tasks based on PRD and User Stories."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing JiraAgent...")
        start_time = time.perf_counter()
        
        # Extract user stories context from context deliverables
        raw_us = context.deliverables.get("User Stories", {})
        if isinstance(raw_us, dict) and "stories" in raw_us:
            user_stories_context = raw_us.get("stories", [])
        elif isinstance(raw_us, dict) and "content" in raw_us:
            user_stories_context = raw_us["content"]
        else:
            user_stories_context = []
            
        user_message = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== PRODUCT REQUIREMENTS DOCUMENT ===
{json.dumps(context.prd, indent=2)}

=== USER STORIES ===
{json.dumps(user_stories_context, indent=2) if user_stories_context else "Not generated yet. Base tasks on the PRD only."}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", JIRA_AGENT_SYSTEM_PROMPT),
            ("user", user_message)
        ]
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            # Clean fences
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
                
            data = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Jira Agent LLM invoke or parse failed: {e}")
            raise RuntimeError(f"Jira Tasks generation failed: {e}") from e
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "JiraAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        new_deliverables = context.deliverables.copy()
        new_deliverables["Jira Tasks"] = {"content": data}
        
        return context.clone(
            deliverables=new_deliverables
        ).add_agent_log(log_entry)

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
