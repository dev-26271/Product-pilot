import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.agents.dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)

CHAT_RESPONSE_PROMPT = """You are a senior Product Manager leading an iterative product refinement.
You have access to the complete workspace context and the user's conversation history.

Analyze the user's message.
1. If the message is a conversational query or request for information (e.g., "Explain how security is handled", "What are the core features?"), answer the user comprehensively and set "is_refinement" to false.
2. If the message contains a request to change, add, delete, or refine the product requirements (e.g., "Add subscription billing", "Target enterprise customers", "Change authentication to SSO"), explain what changes will be applied to the product specs and set "is_refinement" to true.

You MUST respond ONLY with a raw JSON object matching the following structure:
{
  "chat_response": "Your professional PM response or explanation of proposed refinements.",
  "is_refinement": true / false
}

Do not include markdown code fences or conversational text outside the JSON. Return only the valid JSON.
"""

class WorkspaceChatAgent(BaseAgent):
    """Workspace Chat Agent that handles refinement requests or questions about deliverables."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing WorkspaceChatAgent...")
        start_time = time.perf_counter()
        
        chat_history = kwargs.get("chat_history", [])
        user_message = kwargs.get("user_message", "")
        
        # Format chat history context
        history_str = ""
        for msg in chat_history:
            role = "User" if msg["role"] == "user" else "PM"
            history_str += f"{role}: {msg['content']}\n"
            
        user_prompt = f"""=== ACTIVE WORKSPACE SPECS ===
Idea: {context.idea}
Intent: {json.dumps(context.intent_context, indent=2)}
Goals: {json.dumps(context.business_analysis.get("Goals", []), indent=2)}
Features: {json.dumps(context.prd.get("Core_Features", []), indent=2)}

=== CONVERSATION HISTORY ===
{history_str}

=== NEW USER MESSAGE ===
User: {user_message}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", CHAT_RESPONSE_PROMPT),
            ("user", user_prompt)
        ]
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
                
            result_data = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Workspace Chat Agent LLM parse failed: {e}")
            result_data = {
                "chat_response": "I can help you refine the project specs. Please let me know what updates you want to make.",
                "is_refinement": True
            }
            
        is_refinement = bool(result_data.get("is_refinement", False))
        chat_response = result_data.get("chat_response", "")
        
        new_metadata = context.metadata.copy()
        new_metadata["chat_response"] = chat_response
        
        # If it is a refinement request, run the dependency analyzer to find affected components
        if is_refinement:
            analyzer = DependencyAnalyzer()
            affected = analyzer.analyze(user_message)
            new_metadata["pending_changes"] = {
                "instruction": user_message,
                "affected": affected
            }
        else:
            new_metadata.pop("pending_changes", None)
            
        # Standardize chat history storage
        if "chat_history" not in new_metadata:
            new_metadata["chat_history"] = []
        new_metadata["chat_history"].append({"role": "user", "content": user_message})
        new_metadata["chat_history"].append({"role": "assistant", "content": chat_response})
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry = {
            "agent": "WorkspaceChatAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        return context.clone(
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
    
    return {
        "chat_response": result_context.metadata.get("chat_response", ""),
        "pending_changes": result_context.metadata.get("pending_changes"),
        "metadata": result_context.metadata,
        "deliverables": result_context.deliverables
    }


def apply_workspace_refinements(
    workspace_dict: Dict[str, Any],
    instruction: str,
    affected_flags: Dict[str, bool]
) -> Dict[str, Any]:
    """Applies the refinement instruction to parent documents and regenerates affected downstream documents."""
    import copy
    from backend.agents.document_refiner import refine_document
    
    context = WorkspaceContext.from_dict(workspace_dict)
    
    # 1. Update parent documents
    if affected_flags.get("prd"):
        logger.info("Refining Product Requirements Document (PRD) incrementally...")
        current_prd = context.prd
        refined_prd = refine_document(
            document_name="Product Requirements Document (PRD)",
            current_content=current_prd,
            instruction=instruction,
            workspace=context.to_dict()
        )
        context.prd = refined_prd
        context.deliverables["Product Requirements Document (PRD)"] = {"content": refined_prd}
        
    if affected_flags.get("business_analysis"):
        logger.info("Refining Business Analysis incrementally...")
        current_ba = context.business_analysis
        refined_ba = refine_document(
            document_name="Business Analysis",
            current_content=current_ba,
            instruction=instruction,
            workspace=context.to_dict()
        )
        context.business_analysis = refined_ba
        
    # 2. Regenerate affected downstream documents that were already generated (exists in deliverables)
    downstream_mappings = {
        "user_stories": ("User Stories", "user_story"),
        "roadmap": ("Product Roadmap", "roadmap"),
        "jira": ("Jira Tasks", "jira"),
        "sprint_planning": ("Sprint Backlog", "sprint_planning"),
        "brd": ("Business Requirements Document (BRD)", "brd"),
        "srs": ("Software Requirements Specification (SRS)", "srs")
    }
    
    for key, (deliverable_name, agent_registry_key) in downstream_mappings.items():
        if affected_flags.get(key):
            if deliverable_name in context.deliverables:
                logger.info(f"Regenerating downstream deliverable '{deliverable_name}' incrementally...")
                agent = registry.get(agent_registry_key)
                context = agent.execute(context)
                
    # 3. Log version history
    if "version_history" not in context.metadata:
        context.metadata["version_history"] = []
    
    new_version_num = len(context.metadata["version_history"]) + 1
    version_entry = {
        "version": new_version_num,
        "description": instruction,
        "timestamp": datetime.now().isoformat(),
        "deliverables": copy.deepcopy(context.deliverables)
    }
    context.metadata["version_history"].append(version_entry)
    
    # Clear pending changes
    context.metadata.pop("pending_changes", None)
    
    return context.to_dict()
