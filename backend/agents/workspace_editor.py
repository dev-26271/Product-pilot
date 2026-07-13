import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import WORKSPACE_EDITOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class WorkspaceEditorAgent(BaseAgent):
    """Workspace Editor Agent that applies instructions to modify the deliverables directly."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing WorkspaceEditorAgent...")
        start_time = time.perf_counter()
        
        instruction = kwargs.get("instruction", "")
        if not instruction.strip():
            raise ValueError("Refinement instruction cannot be empty.")
            
        context_payload = {
            "name": context.metadata.get("name", "Unknown Project"),
            "idea": context.idea,
            "intent_context": context.intent_context,
            "business_analysis": context.business_analysis,
            "prd": context.prd,
            "deliverables": context.deliverables
        }
        
        user_message = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== ACTIVE WORKSPACE DETAILS ===
{json.dumps(context_payload, indent=2)}

=== REFINE INSTRUCTION ===
{instruction}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", WORKSPACE_EDITOR_SYSTEM_PROMPT),
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
                
            updated_deliverables = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Workspace Editor Agent LLM invoke or parse failed: {e}")
            raise RuntimeError(f"Workspace edit failed: {e}") from e
            
        if "deliverables" in updated_deliverables:
            if isinstance(updated_deliverables["deliverables"], dict):
                updated_deliverables = updated_deliverables["deliverables"]
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "WorkspaceEditorAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        return context.clone(
            deliverables=updated_deliverables
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("workspace_editor", WorkspaceEditorAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def update_workspace(workspace: Dict[str, Any], instruction: str) -> Dict[str, Any]:
    """Public wrapper keeping compatibility with UI triggers."""
    ctx = WorkspaceContext.from_dict(workspace)
    result_context = registry.get("workspace_editor").execute(ctx, instruction=instruction)
    return result_context.to_dict()
