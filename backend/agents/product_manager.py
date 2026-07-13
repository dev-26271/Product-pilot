import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import PRODUCT_MANAGER_SYSTEM_PROMPT
from rag import retrieve_product

logger = logging.getLogger(__name__)

class ProductManagerAgent(BaseAgent):
    """Product Manager Agent that generates or repairs the Product Requirements Document (PRD)."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing ProductManagerAgent...")
        start_time = time.perf_counter()
        
        intent = context.intent_context
        ba = context.business_analysis
        
        # Repair feedback if executing self-repair loop
        repair_feedback = kwargs.get("repair_feedback", "")
        current_prd_draft = kwargs.get("current_prd_draft", {})
        
        # Step 1: Query RAG product database
        problem = intent.get("problem_statement", "")
        features = " ".join(intent.get("core_features", []))
        retrieval_query = f"{problem} {features}".strip() or context.idea
        
        logger.info(f"Retrieving product KB context for query: '{retrieval_query[:50]}...'")
        context_docs = retrieve_product(retrieval_query, k=2)
        context_str = "\n\n".join([doc.page_content for doc in context_docs])
        logger.info(f"Retrieved {len(context_docs)} chunks from product index.")
        
        # Step 2: Build user message
        user_message = f"""Product Context:
{context_str}

Intent Context (Canonical Source of Truth):
{json.dumps(intent, indent=2)}

Business Analysis:
{json.dumps(ba, indent=2)}
"""
        
        if repair_feedback:
            logger.info("Executing repair loop iteration with validation feedback...")
            user_message += f"""

================================================================================
⚠️ REPAIR REQUIRED:
The previous PRD output failed validation.
Validation Feedback:
{repair_feedback}

Current PRD Draft:
{json.dumps(current_prd_draft, indent=2)}

INSTRUCTIONS:
Carefully update the failed sections of the current PRD draft based on the validation feedback.
Do NOT rewrite the whole PRD from scratch. Preserve correct sections exactly.
Return only the complete updated JSON.
================================================================================
"""
        
        # Step 3: Invoke LLM
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", PRODUCT_MANAGER_SYSTEM_PROMPT),
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
                
            pm_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Product Manager LLM invoke or parse failed: {e}")
            if repair_feedback and current_prd_draft:
                pm_json = current_prd_draft
            else:
                pm_json = {
                    "Executive_Summary": intent.get("problem_statement", "Default Executive Summary"),
                    "Product_Vision": "Default Vision",
                    "Problem_Statement": intent.get("problem_statement", "Default Problem"),
                    "Goals_and_Objectives": intent.get("success_metrics", []),
                    "Functional_Requirements": [
                        {
                            "id": "FR-001",
                            "title": "Core System Feature",
                            "description": "The system shall implement core features.",
                            "priority": "High",
                            "acceptance_criteria": "System is accessible."
                        }
                    ],
                    "Non_Functional_Requirements": {"Performance": "Standard response latency"},
                    "Core_Features": [{"name": f, "description": f, "priority": "High", "business_value": "Core benefit"} for f in intent.get("core_features", [])],
                    "Assumptions": [],
                    "Constraints": [],
                    "Success_Metrics": [],
                    "Open_Questions": []
                }
                
        # Validate critical keys
        required_keys = ["Executive_Summary", "Functional_Requirements", "Core_Features", "Success_Metrics"]
        for key in required_keys:
            if key not in pm_json:
                pm_json[key] = [] if key != "Executive_Summary" else "Unknown"
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "ProductManagerAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.90,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        # Assemble standard emoji-keyed PRD structure exactly as orchestrator/UI expects
        
        # 1. Expanded User Personas Formatting
        personas_list = pm_json.get("User_Personas") or ba.get("User Personas", [])
        personas_formatted = []
        for p in personas_list:
            if isinstance(p, dict):
                pname = p.get("name") or p.get("role") or "User Persona"
                prole = p.get("role") or "Persona Role"
                goals = p.get("goals") or [p.get("needs", "")]
                goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)
                pain_points = p.get("pain_points") or []
                pain_str = ", ".join(pain_points) if isinstance(pain_points, list) else str(pain_points)
                
                personas_formatted.append(
                    f"**{pname} ({prole})**\n"
                    f"- *Goals:* {goals_str}\n"
                    f"- *Pain Points:* {pain_str or 'Unknown'}\n"
                    f"- *Motivations:* {p.get('motivations', 'Unknown')}\n"
                    f"- *Technical Proficiency:* {p.get('technical_proficiency', 'Medium')}\n"
                    f"- *Daily Workflow:* {p.get('daily_workflow', 'Unknown')}"
                )
            else:
                personas_formatted.append(str(p))
        personas_md = "\n\n".join(personas_formatted)

        # 2. Detailed Functional Requirements Formatting
        func_reqs_formatted = []
        for r in pm_json.get("Functional_Requirements", []):
            rid = r.get("id", "FR-XXX")
            rtitle = r.get("title") or r.get("name") or "Requirement"
            rdesc = r.get("description", "")
            rpriority = r.get("priority", "Medium")
            rac = r.get("acceptance_criteria", "")
            rpersona = r.get("related_persona", "All")
            rgoal = r.get("related_business_goal", "Unknown")
            rmetric = r.get("success_metric", "Unknown")
            rdeps = r.get("dependencies") or []
            rdeps_str = ", ".join(rdeps) if isinstance(rdeps, list) else str(rdeps)
            rrisks = r.get("risks", "Low")
            
            func_reqs_formatted.append(
                f"**{rid} — {rtitle}** (Priority: {rpriority})\n"
                f"{rdesc}\n"
                f"- *Acceptance Criteria:* {rac}\n"
                f"- *Related Persona:* {rpersona}\n"
                f"- *Related Business Goal:* {rgoal}\n"
                f"- *Success Metric:* {rmetric}\n"
                f"- *Dependencies:* {rdeps_str or 'None'}\n"
                f"- *Risks:* {rrisks}"
            )
        func_reqs_md = "\n\n".join(func_reqs_formatted)

        # 3. Detailed Core Features Formatting
        features_formatted = []
        for f in pm_json.get("Core_Features", []):
            fid = f.get("id", "FR-XXX")
            fname = f.get("name", "Feature")
            fdesc = f.get("description", "")
            fpriority = f.get("priority", "Medium")
            fgoal = f.get("business_goal_mapping", "Unknown")
            fpersona = f.get("user_persona_mapping", "Unknown")
            fmetric = f.get("success_metric", "Unknown")
            fac = f.get("acceptance_criteria", "")
            fdeps = f.get("dependencies") or []
            fdeps_str = ", ".join(fdeps) if isinstance(fdeps, list) else str(fdeps)
            frisks = f.get("risks", "Low")
            
            features_formatted.append(
                f"**{fid} — {fname}** (Priority: {fpriority})\n"
                f"{fdesc}\n"
                f"- *Business Goal Mapping:* {fgoal}\n"
                f"- *User Persona Mapping:* {fpersona}\n"
                f"- *Success Metric:* {fmetric}\n"
                f"- *Acceptance Criteria:* {fac}\n"
                f"- *Dependencies:* {fdeps_str or 'None'}\n"
                f"- *Risks:* {frisks}"
            )
        features_md = "\n\n".join(features_formatted)

        # 4. Detailed High-Level Roadmap Formatting
        roadmap_formatted = []
        for r in pm_json.get("High_Level_Roadmap", []):
            phase = r.get("phase", "Phase")
            objs = r.get("objectives", "Unknown")
            delivs = r.get("deliverables") or []
            delivs_str = ", ".join(delivs) if isinstance(delivs, list) else str(delivs)
            miles = r.get("milestones") or []
            miles_str = ", ".join(miles) if isinstance(miles, list) else str(miles)
            rdeps = r.get("dependencies") or []
            rdeps_str = ", ".join(rdeps) if isinstance(rdeps, list) else str(rdeps)
            metrics = r.get("success_metrics") or []
            metrics_str = ", ".join(metrics) if isinstance(metrics, list) else str(metrics)
            exit_crit = r.get("exit_criteria", "Unknown")
            
            roadmap_formatted.append(
                f"📅 **{phase}**\n"
                f"- *Objectives:* {objs}\n"
                f"- *Deliverables:* {delivs_str}\n"
                f"- *Milestones:* {miles_str}\n"
                f"- *Dependencies:* {rdeps_str or 'None'}\n"
                f"- *Success Metrics:* {metrics_str}\n"
                f"- *Exit Criteria:* {exit_crit}"
            )
        roadmap_md = "\n\n".join(roadmap_formatted)

        # Safe formatting for summary, vision, and problem fields if LLM returned dictionaries or lists
        exec_summary = pm_json.get("Executive_Summary", "")
        if isinstance(exec_summary, dict):
            exec_summary = "\n".join([f"**{k}:** {v}" for k, v in exec_summary.items()])
        elif isinstance(exec_summary, list):
            exec_summary = "\n".join([f"- {item}" for item in exec_summary])
            
        product_vision = pm_json.get("Product_Vision", "")
        if isinstance(product_vision, dict):
            product_vision = "\n".join([f"**{k}:** {v}" for k, v in product_vision.items()])
        elif isinstance(product_vision, list):
            product_vision = "\n".join([f"- {item}" for item in product_vision])

        problem_statement = pm_json.get("Problem_Statement") or exec_summary
        if isinstance(problem_statement, dict):
            problem_statement = "\n".join([f"**{k}:** {v}" for k, v in problem_statement.items()])
        elif isinstance(problem_statement, list):
            problem_statement = "\n".join([f"- {item}" for item in problem_statement])

        prd_content = {
            "📋 Executive Summary":        exec_summary,
            "🔭 Product Vision":            product_vision,
            "🎯 Problem Statement":         problem_statement,
            "👥 User Personas":             personas_md,
            "📈 Goals & Objectives":        "\n".join([f"- {g}" for g in pm_json.get("Goals_and_Objectives", [])]) if isinstance(pm_json.get("Goals_and_Objectives"), list) else str(pm_json.get("Goals_and_Objectives", "")),
            "⚙️ Functional Requirements":  func_reqs_md,
            "🔒 Non-Functional Requirements": "\n".join([f"**{k}:** {v}" for k, v in pm_json.get("Non_Functional_Requirements", {}).items()]) if isinstance(pm_json.get("Non_Functional_Requirements"), dict) else str(pm_json.get("Non_Functional_Requirements", "")),
            "✨ Core Features":             features_md,
            "💡 Assumptions":               "\n".join([f"- {a}" for a in pm_json.get("Assumptions", [])]) if isinstance(pm_json.get("Assumptions"), list) else str(pm_json.get("Assumptions", "")),
            "🚧 Constraints":               "\n".join([f"- {c}" for c in pm_json.get("Constraints", [])]) if isinstance(pm_json.get("Constraints"), list) else str(pm_json.get("Constraints", "")),
            "📊 Success Metrics":           "\n".join([f"- {m}" for m in pm_json.get("Success_Metrics", [])]) if isinstance(pm_json.get("Success_Metrics"), list) else str(pm_json.get("Success_Metrics", "")),
            "📅 High-Level Roadmap":         roadmap_md,
            "❓ Open Questions":            "\n".join([f"- {q}" for q in pm_json.get("Open_Questions", [])]) if isinstance(pm_json.get("Open_Questions"), list) else str(pm_json.get("Open_Questions", ""))
        }
        
        if context.metadata.get("risk_analysis", True):
            prd_content["⚠️ Risk Factors"] = "Initial synchronization intervals and compatibility vectors during client updates."
            
        # Safe string conversions and strip check to prevent 'dict has no attribute strip'
        prd_content = {k: str(v) for k, v in prd_content.items() if v and (str(v).strip() if isinstance(v, str) else True)}
        
        return context.clone(
            prd=pm_json,  # Keep clean JSON inside context
            deliverables={
                "Product Requirements Document (PRD)": {"content": prd_content}
            }
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("product_manager", ProductManagerAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_product_requirements(business_analysis: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the orchestrator & tests."""
    if isinstance(business_analysis, WorkspaceContext):
        result_context = registry.get("product_manager").execute(business_analysis)
        return result_context.prd
    elif isinstance(business_analysis, dict) and "business_analysis" in business_analysis:
        ctx = WorkspaceContext.from_dict(business_analysis)
        result_context = registry.get("product_manager").execute(ctx)
        return result_context.prd
    else:
        # Legacy direct payload format
        ctx = WorkspaceContext()
        ctx.business_analysis = business_analysis
        ctx.intent_context = {
            "project_name": "Legacy Project",
            "problem_statement": business_analysis.get("Problem Statement", "Default Problem"),
            "core_features": []
        }
        result_context = registry.get("product_manager").execute(ctx)
        return result_context.prd
