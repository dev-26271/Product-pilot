import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import ROADMAP_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class RoadmapAgent(BaseAgent):
    """Roadmap Agent that generates the Product Roadmap based on PRD and Epics."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing RoadmapAgent...")
        start_time = time.perf_counter()
        
        # User Stories might be stored in context.deliverables
        raw_us = context.deliverables.get("User Stories", {})
        if isinstance(raw_us, dict) and "epics" in raw_us:
            us_epics_context = raw_us.get("epics", [])
        else:
            us_epics_context = []
            
        user_message = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== PRODUCT REQUIREMENTS DOCUMENT ===
{json.dumps(context.prd, indent=2)}

=== USER STORY EPICS ===
{json.dumps(us_epics_context, indent=2) if us_epics_context else "Not generated yet. Build roadmap from the PRD only."}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", ROADMAP_AGENT_SYSTEM_PROMPT),
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
            logger.error(f"Roadmap Agent LLM invoke or parse failed: {e}")
            raise RuntimeError(f"Roadmap generation failed: {e}") from e
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "RoadmapAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        new_deliverables = context.deliverables.copy()
        new_deliverables["Product Roadmap"] = {"content": data}
        
        return context.clone(
            deliverables=new_deliverables
        ).add_agent_log(log_entry)

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
