import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import SRS_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class SRSAgent(BaseAgent):
    """SRS Agent that generates the Software Requirements Specification (SRS) using Intent and PRD."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing SRSAgent...")
        start_time = time.perf_counter()
        
        user_message = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== PRODUCT REQUIREMENTS DOCUMENT ===
{json.dumps(context.prd, indent=2)}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", SRS_AGENT_SYSTEM_PROMPT),
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
            logger.error(f"SRS Agent LLM invoke or parse failed: {e}")
            raise RuntimeError(f"SRS generation failed: {e}") from e
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "SRSAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        new_deliverables = context.deliverables.copy()
        new_deliverables["Software Requirements Specification (SRS)"] = {"content": data}
        
        return context.clone(
            deliverables=new_deliverables
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("srs", SRSAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_srs(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("srs").execute(workspace)
        return result_context.deliverables["Software Requirements Specification (SRS)"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("srs").execute(ctx)
        return result_context.deliverables["Software Requirements Specification (SRS)"]["content"]
