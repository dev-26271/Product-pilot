import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import WORKSPACE_CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class WorkspaceChatAgent(BaseAgent):
    """Workspace Chat Agent that handles refinement requests or questions about deliverables."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing WorkspaceChatAgent...")
        start_time = time.perf_counter()
        
        chat_history = kwargs.get("chat_history", [])
        user_message = kwargs.get("user_message", "")
        
        # Prepare context payload
        context_payload = {
            "name": context.metadata.get("name", "Unknown Project"),
            "idea": context.idea,
            "intent_context": context.intent_context,
            "business_analysis": context.business_analysis,
            "prd": context.prd,
            "deliverables": context.deliverables
        }
        
        # Format chat history context
        history_str = ""
        for msg in chat_history:
            role = "User" if msg["role"] == "user" else "Senior PM"
            history_str += f"{role}: {msg['content']}\n"
            
        user_prompt = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== ACTIVE WORKSPACE DETAILS ===
{json.dumps(context_payload, indent=2)}

=== CONVERSATION HISTORY ===
{history_str}

=== NEW USER MESSAGE ===
User: {user_message}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", WORKSPACE_CHAT_SYSTEM_PROMPT),
            ("user", user_prompt)
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
                
            result_data = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Workspace Chat Agent LLM invoke or parse failed: {e}")
            raise RuntimeError(f"Chat refinement failed: {e}") from e
            
        # Validate expected keys
        required_keys = ["chat_response", "updated_tabs", "deliverables"]
        for key in required_keys:
            if key not in result_data:
                logger.warning(f"Key '{key}' is missing from PM chat response JSON.")
                
        # Robustly handle double-nested deliverables
        if "deliverables" in result_data:
            deliv = result_data["deliverables"]
            if "deliverables" in deliv:
                result_data["deliverables"] = deliv["deliverables"]
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "WorkspaceChatAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        # Return context cloned with updated deliverables and chat response stored in metadata for UI retrieval
        new_metadata = context.metadata.copy()
        new_metadata["chat_response"] = result_data.get("chat_response", "")
        new_metadata["updated_tabs"] = result_data.get("updated_tabs", [])
        
        return context.clone(
            deliverables=result_data.get("deliverables", context.deliverables),
            metadata=new_metadata
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("workspace_chat", WorkspaceChatAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def chat_refine_workspace(
    workspace: Dict[str, Any], 
    chat_history: List[Dict[str, str]], 
    user_message: str
) -> Dict[str, Any]:
    """Public wrapper keeping compatibility with UI chat triggers."""
    ctx = WorkspaceContext.from_dict(workspace)
    result_context = registry.get("workspace_chat").execute(
        ctx, 
        chat_history=chat_history, 
        user_message=user_message
    )
    
    # Return formatted result containing deliverables, chat_response, and updated_tabs
    return {
        "chat_response": result_context.metadata.get("chat_response", ""),
        "updated_tabs": result_context.metadata.get("updated_tabs", []),
        "deliverables": result_context.deliverables
    }
