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

2. SPECIFIC SCENARIO INSTRUCTIONS:
- Roadmap Explanation: Detail the phases, objectives, milestones, success metrics, and exit criteria in the Product Roadmap.
- Project Summary: Synthesize the problem statement, SMART business goals, user personas, and core features.
- Cost Estimation: Calculate a realistic team size, timeline, cloud infra, dev cost, and annual maintenance. All cost estimations and monetary figures MUST be in Indian Rupees (INR, symbol: ₹). State assumptions and confidence clearly.
- Risk Analysis: Analyze risk factors from the PRD, business goals, and validation reports.
- Scope Reduction: Recommend which features or requirements can be postponed to later roadmap phases.
- Primary Users: Present the personas (goals, role, motivations, and workflow).

3. SOURCE ATTRIBUTION:
At the bottom of your response, always list the specific sources from the WorkspaceContext that you used to formulate your answer under a '**Source:**' header. Format as:
**Source:**
- [Deliverable Name] → [Specific Section or Entity ID]
Example:
**Source:**
- PRD → Functional Requirements (FR-001)

4. GREETINGS & PLACEHOLDERS FORBIDDEN:
- NEVER output generic introductory sentences, greeting fluff (like "Sure, I can help you with...", "Hello! As a Senior PM..."), or placeholders like "I can help...".
- Answer the query directly and professionally using the workspace.

5. CONVERSATIONAL VS. MODIFICATION CLASSIFICATION:
  - You must classify the user's query into one of these specific intent categories:
    - 'Question': General questions, inquiries, or checks on workspace consistency.
    - 'Summarize': Requests for a summary of the project, features, goals, or personas.
    - 'Explain': Requests to explain the roadmap, system requirements, or features.
    - 'Estimate Cost': Development cost, timeline, resource sizing, or annual cloud pricing.
    - 'Modify PRD': User explicitly requests additions, edits, removals of functional/non-functional requirements or core features.
    - 'Modify Roadmap': User requests changes to roadmap releases, quarters, or milestones.
    - 'Modify User Stories': User requests custom updates or additions to user stories.
  - Set the "intent" field in JSON to one of these category names.
  - Set "is_refinement" to true ONLY if the intent is 'Modify PRD', 'Modify Roadmap', or 'Modify User Stories'. For informational intents ('Question', 'Summarize', 'Explain', 'Estimate Cost'), set "is_refinement" to false.

You MUST respond ONLY with a raw JSON object matching the following structure:
{
  "chat_response": "Your professional PM response, formatted beautifully with markdown. If recommending, use the structured layout. Must include a 'Source:' section at the bottom.",
  "intent": "Question / Summarize / Explain / Estimate Cost / Modify PRD / Modify Roadmap / Modify User Stories",
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

def _fallback_chat_response(context: WorkspaceContext, user_message: str) -> Dict[str, Any]:
    """Generates a workspace-aware fallback response when the LLM call fails."""
    msg = user_message.lower()
    
    # 1. Who are the primary users?
    if "user" in msg or "persona" in msg:
        personas = context.business_analysis.get("user_personas", [])
        if not personas and "User Personas" in context.deliverables:
            personas = context.deliverables.get("User Personas", {})
        
        if personas:
            p_list = []
            if isinstance(personas, list):
                for p in personas:
                    if isinstance(p, dict):
                        name = p.get("name", "User")
                        role = p.get("role", "")
                        goals = ", ".join(p.get("goals", [])) if isinstance(p.get("goals"), list) else str(p.get("goals", ""))
                        p_list.append(f"- **{name}** ({role}): Goals: {goals}")
            elif isinstance(personas, dict) and "entities" in personas:
                for p in personas.get("entities", {}).get("user_personas", []):
                    name = p.get("name", "User")
                    role = p.get("role", "")
                    goals = ", ".join(p.get("goals", []))
                    p_list.append(f"- **{name}** ({role}): Goals: {goals}")
            elif isinstance(personas, dict) and "content" in personas:
                content = personas.get("content", {})
                for k, v in content.items():
                    p_list.append(f"- **{k}**:\n{v}")
            
            if p_list:
                return {
                    "chat_response": "### Primary Users (Fallback Mode)\n\nHere are the primary users defined in the workspace:\n\n" + "\n".join(p_list) + "\n\n**Source:**\n- Business Analysis → User Personas",
                    "is_refinement": False
                }
            
    # 2. Explain this roadmap
    if "roadmap" in msg:
        roadmap = context.deliverables.get("Product Roadmap", {})
        content = roadmap.get("content", {})
        if content:
            roadmap_md = "\n\n".join([f"**{k}**:\n{v}" for k, v in content.items()])
            return {
                "chat_response": f"### Product Roadmap (Fallback Mode)\n\n{roadmap_md}\n\n**Source:**\n- Roadmap → Content",
                "is_refinement": False
            }
            
    # 3. Development Cost Estimation
    if "cost" in msg or "estimat" in msg or "budget" in msg:
        features = context.intent_context.get("core_features", [])
        num_features = len(features) if features else 3
        team_size = max(3, num_features * 2)
        timeline_months = max(3, num_features * 1.5)
        # Assuming average developer rate of ₹1,50,000/month in INR
        dev_cost = team_size * timeline_months * 150000
        cloud_cost = timeline_months * 25000
        maint_cost = dev_cost * 0.20
        
        return {
            "chat_response": f"""### Development Cost Estimation (Fallback Mode)
 
Based on the core features and scope in the active workspace, here is a preliminary cost estimation in Indian Rupees (INR):
 
- **Estimated Team Size:** {team_size} members (Developers, PM, QA, Designer)
- **Estimated Timeline:** {timeline_months:.1f} months
- **Software Development Cost:** ₹{dev_cost:,.2f}
- **Cloud Infrastructure Cost:** ₹{cloud_cost:,.2f} (during development)
- **Annual Maintenance Cost:** ₹{maint_cost:,.2f}
 
**Assumptions:**
1. Mixed engineering team (average rate of ₹1,50,000/month per FTE).
2. Clean integration APIs exist for any required external ERP or dependency systems.
3. Standard cloud resources (AWS/GCP) hosting without high-end GPU or enterprise database licenses.
 
*Confidence: 75%*
 
**Source:**
- Intent Context → Core Features""",
            "is_refinement": False
        }
        
    # 4. What risks do you see? / Analyze risks
    if "risk" in msg:
        prd = context.prd or {}
        risk_list = []
        if isinstance(prd, dict) and "Executive_Summary" in prd:
            risk_list = prd.get("Executive_Summary", {}).get("risks", [])
        
        if not risk_list:
            risk_list = ["Integration complexity with legacy ERP/EHR systems.", "User adoption friction during transition from manual flows."]
            
        r_str = "\n".join([f"- {r}" for r in risk_list])
        return {
            "chat_response": f"### Risk Analysis (Fallback Mode)\n\nHere are the active risks identified in the workspace deliverables:\n\n{r_str}\n\n**Source:**\n- PRD → Executive Summary (Risks)",
            "is_refinement": False
        }
        
    # 5. Summarize this project / Explain this project
    if "summar" in msg or "explain" in msg or "project" in msg:
        idea = context.idea
        prob = context.business_analysis.get("problem_statement", {}).get("text", "") if isinstance(context.business_analysis, dict) else ""
        goals = context.business_analysis.get("business_goals", []) if isinstance(context.business_analysis, dict) else []
        g_list = [f"- Goal {g.get('id', 'BG-?')}: {g.get('goal')}" for g in goals if isinstance(g, dict) and g.get('goal')]
        g_str = "\n".join(g_list)
        return {
            "chat_response": f"### Project Summary (Fallback Mode)\n\n**Product Idea:** {idea}\n\n**Problem:** {prob or idea}\n\n**Business Goals:**\n{g_str or '- Core product launch'}\n\n**Source:**\n- Business Analysis → Problem Statement & Goals",
            "is_refinement": False
        }
        
    # 6. Scope Reduction / Reduce MVP scope
    if "reduce" in msg or "scope" in msg or "mvp" in msg:
        features = context.intent_context.get("core_features", [])
        if features:
            postpone = features[-1]
            keep = features[:-1]
            keep_str = "\n".join([f"- {f}" for f in keep])
            return {
                "chat_response": f"### MVP Scope Reduction Recommendation (Fallback Mode)\n\nTo compress the timeline and reduce scope, I recommend keeping these core features in the MVP:\n{keep_str}\n\nAnd postponing this feature to Phase 2:\n- **{postpone}**\n\n**Source:**\n- Intent Context → Core Features",
                "is_refinement": False
            }
            
    # Default fallback
    return {
        "chat_response": f"### Workspace Assistant (Fallback Mode)\n\nI am currently operating in offline/fallback mode. Here are the details of the active workspace **{context.idea[:60]}...**:\n\n- **Project Idea:** {context.idea}\n- **PRD status:** {'Compiled' if context.prd else 'Not compiled'}\n- **Deliverables:** {', '.join(context.deliverables.keys()) if context.deliverables else 'None generated'}\n\n*Please let me know if you would like me to explain the roadmap, summarize the project, estimate costs, analyze risks, list primary users, or suggest scope reductions.*",
        "is_refinement": False
    }


class WorkspaceChatAgent(BaseAgent):
    """Workspace Chat Agent that handles refinement requests or questions about deliverables."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing WorkspaceChatAgent...")
        start_time = time.perf_counter()
        
        chat_history = kwargs.get("chat_history", [])
        user_message = kwargs.get("user_message", "")
        
        # 1. Deterministic check for Undo / Restore Version History commands
        import re
        msg_lower = user_message.strip().lower()
        is_undo = msg_lower in ["undo", "restore previous version", "go back", "revert", "restore version"]
        target_ver = None
        
        match = re.search(r'restore version\s+(\d+)', msg_lower)
        if match:
            is_undo = True
            target_ver = int(match.group(1))
            
        if is_undo:
            version_history = context.metadata.get("version_history", [])
            if not version_history:
                chat_response = "### Undo Command (Fallback Mode)\n\nNo version history was found for this workspace."
            else:
                if target_ver is None:
                    # Find previous version
                    if len(version_history) > 1:
                        target_ver = len(version_history) - 1
                    else:
                        chat_response = "### Undo Command (Fallback Mode)\n\nYou are currently at the first version of this workspace. Cannot undo further."
                        
                if target_ver is not None:
                    from backend.version_history import rebuild_workspace_version, VersionControl
                    try:
                        restored_ws = rebuild_workspace_version(version_history, target_ver)
                        if restored_ws:
                            restored_ws = VersionControl.create_version(
                                restored_ws,
                                action=f"Rollback to Version {target_ver}",
                                summary=f"Restored previous workspace state (Version {target_ver}) via chat command.",
                                author="User"
                            )
                            # Update context with the restored state
                            context.idea = restored_ws.get("idea", "")
                            context.prd = restored_ws.get("prd", {})
                            context.business_analysis = restored_ws.get("business_analysis", {})
                            context.deliverables = restored_ws.get("deliverables", {})
                            context.metadata = restored_ws.get("metadata", {})
                            
                            chat_response = f"### Workspace Restored (Version {target_ver})\n\nI have successfully restored the workspace state back to Version {target_ver}. All history has been preserved, and Version {len(version_history)} was created.\n\n**Source:**\n- Version History → Version {target_ver}"
                        else:
                            chat_response = f"### Undo Command (Fallback Mode)\n\nFailed to locate Version {target_ver} in the workspace history."
                    except Exception as e:
                        chat_response = f"### Undo Command (Fallback Mode)\n\nError restoring version {target_ver}: {e}"
            
            # Formulate the returned updated context
            new_metadata = context.metadata.copy()
            new_metadata["chat_response"] = chat_response
            new_metadata.pop("pending_changes", None)
            new_metadata.pop("pending_approval", None)
            new_metadata.pop("pending_impact", None)
            
            # Standardize chat history storage
            if "chat_history" not in new_metadata or not new_metadata["chat_history"]:
                new_metadata["chat_history"] = list(chat_history)
            new_metadata["chat_history"].append({"role": "user", "content": user_message})
            new_metadata["chat_history"].append({
                "role": "assistant", 
                "content": chat_response,
                "reasoning_trace": "Deterministic Undo / Rollback Handler"
            })
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            log_entry = {
                "agent": "WorkspaceChatAgent",
                "model": "Deterministic Undo Handler",
                "latency_ms": duration_ms,
                "tokens": 0,
                "confidence": 1.0,
                "timestamp": datetime.now().isoformat(),
                "version": "3.0.0"
            }
            return context.clone(metadata=new_metadata).add_agent_log(log_entry)
        
        # Build prompt payload with active workspace context
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

=== NEW USER MESSAGE ===
User: {user_message}
"""
        
        # Build messages block utilizing conversational memory blocks natively
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", ASK_PRODUCTPILOT_SYSTEM_PROMPT)
        ]
        
        for msg in chat_history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                messages.append(("user", content))
            elif role in ["assistant", "pm"]:
                messages.append(("assistant", content))
                
        messages.append(("user", user_prompt))
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            result_data = json.loads(raw_text, strict=False)
        except Exception as e:
            logger.error(f"Workspace Chat Agent LLM invoke or parse failed: {e}. Running fallback reasoning...")
            result_data = _fallback_chat_response(context, user_message)
            
        intent = result_data.get("intent", "Question")
        is_refinement = intent in ["Modify PRD", "Modify Roadmap", "Modify User Stories"]
        chat_response = result_data.get("chat_response", "")
        
        new_metadata = context.metadata.copy()
        new_metadata["chat_response"] = chat_response
        
        # If it is a refinement request, run the Change Impact Analysis
        if is_refinement:
            impact_agent = registry.get("impact_analysis")
            context = impact_agent.execute(context, instruction=user_message)
            new_metadata = context.metadata.copy()
            new_metadata.pop("pending_changes", None)
            new_metadata.pop("pending_approval", None)
        else:
            new_metadata.pop("pending_impact", None)
            new_metadata.pop("pending_changes", None)
            new_metadata.pop("pending_approval", None)
            
        # Standardize chat history storage
        if "chat_history" not in new_metadata or not new_metadata["chat_history"]:
            new_metadata["chat_history"] = list(chat_history)
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
            "version": "3.0.0"
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
                logger.info(f"Refining downstream deliverable '{deliverable_name}' incrementally...")
                agent = registry.get(agent_registry_key)
                context = agent.execute(context, mode="update", instruction=instruction)
                
    # 3. Log version history using VersionControl
    from backend.version_history import VersionControl
    context_dict = context.to_dict()
    context_dict = VersionControl.create_version(
        context_dict,
        action="Refinement Applied",
        summary=f"Refinement: {instruction}",
        author="User"
    )
    context = WorkspaceContext.from_dict(context_dict)
    new_version_num = len(context.metadata.get("version_history", []))
    
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

    # Run Validation Agent conditionally: only for wide structural changes
    num_affected = sum(1 for v in affected_flags.values() if v)
    needs_semantic_val = (
        affected_flags.get("business_analysis") or
        affected_flags.get("roadmap") or
        num_affected > 2
    )
    
    if needs_semantic_val:
        logger.info("Structural changes detected. Invoking ValidationAgent for semantic validation...")
        validation_agent = registry.get("validation_agent")
        try:
            context = validation_agent.execute(context)
            logger.info("Validation Agent successfully verified workspace integrity after refinement.")
        except Exception as e:
            logger.error(f"Validation Agent verification failed: {e}")
    else:
        logger.info("Minor edits detected. Skipping ValidationAgent semantic checks (deterministic validation only).")

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
