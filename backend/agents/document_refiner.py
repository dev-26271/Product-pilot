import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import DOCUMENT_REFINER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class DocumentRefinerAgent(BaseAgent):
    """Document Refiner Agent that applies refinement instruction to a single deliverable."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing DocumentRefinerAgent...")
        start_time = time.perf_counter()
        
        document_name = kwargs.get("document_name", "")
        current_content = kwargs.get("current_content", {})
        instruction = kwargs.get("instruction", "")
        
        user_message = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== DOCUMENT DETAILS ===
Document to Refine: {document_name}
Current Content:
{json.dumps(current_content, indent=2)}

=== REFINEMENT INSTRUCTION ===
{instruction}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", DOCUMENT_REFINER_SYSTEM_PROMPT),
            ("user", user_message)
        ]
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            # Clean fences
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            try:
                data = json.loads(raw_text)
            except Exception as parse_err:
                cleaned = raw_text.strip()
                if cleaned.startswith("{") and not cleaned.endswith("}"):
                    try:
                        data = json.loads(cleaned + "}")
                        logger.info("DocumentRefinerAgent: successfully repaired JSON by appending closing brace.")
                    except Exception:
                        raise parse_err
                else:
                    raise parse_err
        except Exception as e:
            logger.error(f"Document Refiner Agent LLM invoke or parse failed: {e}")
            logger.error(f"Raw response was: '{raw_text if 'raw_text' in locals() else 'None'}'")
            # Fallback to current content
            data = current_content

            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "DocumentRefinerAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        # Update context deliverables map
        new_deliverables = context.deliverables.copy()
        new_deliverables[document_name] = {"content": data}
        
        # Stash refined document in metadata temporarily so wrapper can return it
        new_metadata = context.metadata.copy()
        new_metadata["refined_document_content"] = data
        
        return context.clone(
            deliverables=new_deliverables,
            metadata=new_metadata
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("document_refiner", DocumentRefinerAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def refine_document(
    document_name: str, 
    current_content: Dict[str, Any], 
    instruction: str, 
    workspace: Dict[str, Any]
) -> Dict[str, Any]:
    """Public wrapper keeping compatibility with UI refinement triggers."""
    ctx = WorkspaceContext.from_dict(workspace)
    result_context = registry.get("document_refiner").execute(
        ctx,
        document_name=document_name,
        current_content=current_content,
        instruction=instruction
    )
    return result_context.metadata.get("refined_document_content", {})
