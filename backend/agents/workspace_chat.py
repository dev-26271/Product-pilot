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

ASK_PRODUCTPILOT_SYSTEM_PROMPT = """You are a Principal Product Manager leading a product workspace refinement.
You have access to the complete workspace context (Idea, Intent, Business Analysis, PRD, User Stories, Roadmap, Jira Tasks, Traceability Graph, and Validation Results) and the user's conversation history.

Analyze the user's message and follow these rules:

1. UNDERSTANDING, ANALYSIS & CRITIQUE:
- You must reason over the existing workspace context rather than inventing information.
- Use the Traceability Graph before answering to identify structural relationships between business goals, personas, features, requirements, user stories, and tasks.
- Reference existing entity IDs (e.g. BG-001, FT-001, FR-001, PE-001, US-001, JT-001). Never invent relationships or IDs.
- If the workspace lacks enough information to answer a question or perform an analysis, explicitly state that.

2. STRUCTURED RECOMMENDATIONS:
When providing strategic recommendations or critique, you MUST structure your response (within the JSON chat_response string) to include the following sections (formatted as markdown):
- **Reasoning**: Why you are making this recommendation (gap or opportunity).
- **Business Impact**: Impact on KPIs, target values, and personas.
- **Engineering Impact**: Impact on story points, developer tasks, or complexity.
- **Risks**: Potential downstream risks or release risks.
- **Recommendation**: Your concrete, actionable proposal.
- **Confidence**: A numeric confidence rating between 0% and 100%.

3. CONVERSATIONAL VS. MODIFICATION CLASSIFICATION:
- If the user's message is a conversational query, critique, or request for information (e.g., "Summarize this project", "Are there inconsistencies?", "Which requirements have weak ACs?", "Suggest MVP scope"), answer the user comprehensively and set "is_refinement" to false.
- If the user explicitly requests changes, additions, deletions, or scope modifications (e.g., "Add subscription billing", "Remove drone delivery", "Change authentication to SSO"), explain the proposed changes and set "is_refinement" to true.

You MUST respond ONLY with a raw JSON object matching the following structure:
{
  "chat_response": "Your professional PM response, formatted beautifully with markdown. If recommending, use the structured layout.",
  "is_refinement": true / false,
  "reasoning_trace": {
    "sources_consulted": ["Business Analysis", "PRD", "User Stories", "Validation Report"],
    "entities_referenced": ["BG-002", "FR-004"],
    "traceability_chain": ["BG-002 -> FR-004 -> US-011"],
    "validation_checks": ["No inconsistencies detected."],
    "confidence": 0.95,
    "affected_documents": ["User Stories"],
    "affected_entities": ["US-011"],
    "estimated_changes": "Describe the scope of the updates.",
    "validation_required": "Describe the validation checks that must run.",
    "recommended_action": "Describe the recommended path to apply updates."
  }
}

Do not include markdown code fences (like ```json) or conversational text outside the JSON. Return only the valid JSON.
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
            
        # Assemble complete WorkspaceContext payload for the LLM
        user_prompt = f"""=== ACTIVE WORKSPACE SPECS ===
Product Idea: {context.idea}

Intent Context:
{json.dumps(context.intent_context, indent=2)}

Business Analysis:
{json.dumps(context.business_analysis, indent=2)}

Product Requirements Document (PRD):
{json.dumps(context.prd, indent=2)}

Deliverables (User Stories, Roadmap, Jira Tasks):
{json.dumps({k: v for k, v in context.deliverables.items() if k not in ["Business Analysis", "Product Requirements Document (PRD)"]}, indent=2)}

Traceability Graph:
{json.dumps(context.metadata.get("entity_graph", {}), indent=2)}

Validation Results:
{json.dumps(context.metadata.get("validation_report", {}), indent=2)}

=== CONVERSATION HISTORY ===
{history_str}

=== NEW USER MESSAGE ===
User: {user_message}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", ASK_PRODUCTPILOT_SYSTEM_PROMPT),
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
                
            result_data = json.loads(raw_text, strict=False)
        except Exception as e:
            logger.error(f"Workspace Chat Agent LLM parse failed: {e}")
            if 'raw_text' in locals():
                logger.error(f"Raw text that failed parsing:\n{raw_text}")
            result_data = {
                "chat_response": "I can help you analyze, critique, or modify the project deliverables. Please ask me a question or suggest updates.",
                "is_refinement": False
            }
            
        is_refinement = bool(result_data.get("is_refinement", False))
        chat_response = result_data.get("chat_response", "")
        
        new_metadata = context.metadata.copy()
        new_metadata["chat_response"] = chat_response
        
        # If it is a refinement request, run the Change Impact Analysis
        if is_refinement:
            impact_agent = registry.get("impact_analysis")
            context = impact_agent.execute(context, instruction=user_message)
            new_metadata = context.metadata.copy()
            # Clear legacy variables to prevent collisions
            new_metadata.pop("pending_changes", None)
            new_metadata.pop("pending_approval", None)
        else:
            new_metadata.pop("pending_impact", None)
            new_metadata.pop("pending_changes", None)
            new_metadata.pop("pending_approval", None)
            
        # Standardize chat history storage
        if "chat_history" not in new_metadata:
            new_metadata["chat_history"] = []
        new_metadata["chat_history"].append({"role": "user", "content": user_message})
        new_metadata["chat_history"].append({
            "role": "assistant", 
            "content": chat_response,
            "reasoning_trace": result_data.get("reasoning_trace")
        })
        
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
        "pending_impact": result_context.metadata.get("pending_impact"),
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
    
    from backend.version_history import compute_workspace_diff, rebuild_workspace_version
    
    # Rebuild previous version to diff against
    try:
        old_ws = rebuild_workspace_version(context.metadata["version_history"], new_version_num - 1)
    except Exception as e:
        logger.error(f"Failed to rebuild previous version: {e}")
        old_ws = {}
        
    # Find modified entities and documents from pending impact
    pending_impact = context.metadata.get("pending_impact") or {}
    modified_entities = [ent.get("id") if isinstance(ent, dict) else str(ent) for ent in pending_impact.get("affected_entities", [])]
    changed_documents = pending_impact.get("affected_documents", [])
    
    # Validation status
    val_report = context.metadata.get("validation_report", {})
    val_status = {
        "valid": val_report.get("valid", True),
        "score": val_report.get("overall_score", 1.0),
        "errors": val_report.get("errors", []),
        "warnings": val_report.get("warnings", [])
    }
    
    # Snapshot the complete context state, excluding circular / transient references
    snapshot_ctx = context.clone()
    snapshot_ctx.metadata.pop("pending_changes", None)
    snapshot_ctx.metadata.pop("pending_approval", None)
    snapshot_ctx.metadata.pop("pending_impact", None)
    snapshot_dict = snapshot_ctx.to_dict()
    
    if old_ws:
        delta = compute_workspace_diff(old_ws, snapshot_dict)
        version_entry = {
            "version": new_version_num,
            "description": instruction,
            "timestamp": datetime.now().isoformat(),
            "modified_entities": modified_entities,
            "changed_documents": changed_documents,
            "validation_status": val_status,
            "summary": f"Refinement: {instruction[:100]}...",
            "delta": delta
        }
    else:
        # Fallback to full snapshot
        version_entry = {
            "version": new_version_num,
            "description": instruction,
            "timestamp": datetime.now().isoformat(),
            "modified_entities": modified_entities,
            "changed_documents": changed_documents,
            "validation_status": val_status,
            "summary": f"Refinement: {instruction[:100]}...",
            "snapshot": snapshot_dict
        }
        
    context.metadata["version_history"].append(version_entry)
    
    # 4. Log to Decision Log
    if "decision_log" not in context.metadata:
        context.metadata["decision_log"] = []
        
    decision_entry = {
        "id": f"DEC-{len(context.metadata['decision_log']) + 1:03d}",
        "timestamp": datetime.now().isoformat(),
        "agent": "WorkspaceChatAgent",
        "reason": instruction,
        "user_approval": True,
        "affected_documents": [doc for doc, affected in affected_flags.items() if affected],
        "rollback_version": new_version_num
    }
    context.metadata["decision_log"].append(decision_entry)
    
    # Rebuild entity graph and persistent ID mappings
    from backend.agents.traceability_engine import TraceabilityEngine
    engine = TraceabilityEngine(context.to_dict())
    context.metadata["entity_graph"] = engine.metadata.get("entity_graph", {})
    context.metadata["id_mappings"] = engine.metadata.get("id_mappings", {})

    # Run Validation Agent to verify dependency integrity
    validation_agent = registry.get("validation_agent")
    try:
        context = validation_agent.execute(context)
        logger.info("Validation Agent successfully verified workspace integrity after refinement.")
    except Exception as e:
        logger.error(f"Validation Agent verification failed: {e}")

    # Refresh planning analysis deterministically after refinements and validation
    try:
        from backend.agents.entity_schema import calculate_planning_analysis
        context.metadata["planning_analysis"] = calculate_planning_analysis(context)
        logger.info("Dynamic planning analysis refreshed successfully after refinement.")
    except Exception as e:
        logger.error(f"Failed to refresh dynamic planning analysis: {e}")

    # Clear pending refinements
    context.metadata.pop("pending_changes", None)
    context.metadata.pop("pending_impact", None)
    
    return context.to_dict()
