import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import PRODUCT_MANAGER_SYSTEM_PROMPT
from backend.agents.entity_schema import (
    validate_entity_envelope, validate_domain_fields,
    FEATURE_REQUIRED, FUNCTIONAL_REQUIREMENT_REQUIRED
)
from rag import retrieve_product

logger = logging.getLogger(__name__)

class ProductManagerAgent(BaseAgent):
    """Product Manager Agent that generates or repairs the Product Requirements Document (PRD)."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing ProductManagerAgent...")
        start_time = time.perf_counter()
        
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()
        
        intent = context.intent_context
        ba = context.business_analysis
        
        # Repair feedback if executing self-repair loop
        repair_feedback = kwargs.get("repair_feedback", "")
        current_prd_draft = kwargs.get("current_prd_draft", {})
        
        # Step 1: Query RAG product database
        profiler.start_sub("RAG Loading & Search")
        problem = intent.get("problem_statement", "")
        features = " ".join(intent.get("core_features", []))
        retrieval_query = f"{problem} {features}".strip() or context.idea
        
        logger.info(f"Retrieving product KB context for query: '{retrieval_query[:50]}...'")
        context_docs = retrieve_product(retrieval_query, k=2)
        context_str = "\n\n".join([doc.page_content for doc in context_docs])
        logger.info(f"Retrieved {len(context_docs)} chunks from product index.")
        profiler.end_sub("RAG Loading & Search")
        
        # Step 2: Build user message
        profiler.start_sub("Prompt Construction")
        user_message = f"""Product Context:
{context_str}

Intent Context (Canonical Source of Truth):
{json.dumps(intent, indent=2)}

Business Analysis:
{json.dumps(ba, indent=2)}

Current UTC timestamp: {datetime.now(timezone.utc).isoformat()}
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
        profiler.end_sub("Prompt Construction")
        
        profiler.start_sub("LLM Invocation")
        raw_text = ""
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            profiler.end_sub("LLM Invocation")
            
            # Clean fences
            profiler.start_sub("Response Parsing")
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
                
            pm_json = json.loads(raw_text)
            profiler.end_sub("Response Parsing")
        except Exception as e:
            profiler.end_sub("LLM Invocation")
            profiler.end_sub("Response Parsing")
            logger.error(f"Product Manager LLM invoke or parse failed: {e}")
            if repair_feedback and current_prd_draft:
                pm_json = current_prd_draft
            else:
                industry_val = intent.get("industry", {})
                if isinstance(industry_val, dict):
                    ind_name = industry_val.get("value") or "Target"
                else:
                    ind_name = str(industry_val) if industry_val else "Target"
                    
                prod_val = intent.get("product_type", {})
                if isinstance(prod_val, dict):
                    prod_name = prod_val.get("value") or "Platform"
                else:
                    prod_name = str(prod_val) if prod_val else "Platform"
                    
                aud_val = intent.get("audience", {})
                if isinstance(aud_val, dict):
                    aud_name = aud_val.get("value") or "Users"
                else:
                    aud_name = str(aud_val) if aud_val else "Users"
                
                generated_vision = f"To build a state-of-the-art {prod_name.lower()} that simplifies processes and enhances capabilities for {aud_name.lower()} in the {ind_name.lower()} market."
 
                
                raw_features = intent.get("core_features", [])
                if not raw_features:
                    raw_features = ["Core System Dashboard", "Automated Event Logging", "Secure Data API Integration"]
                    
                fallback_features = []
                for i, f in enumerate(raw_features):
                    fallback_features.append({
                        "id": f"FT-{str(i+1).zfill(3)}",
                        "name": f,
                        "description": f"Provides automated capability for {f.lower()}.",
                        "priority": "High",
                        "business_value": "Addresses the core target problem and guarantees seamless operational flow.",
                        "user_persona_mapping": "PE-001",
                        "business_goal_mapping": "BG-001",
                        "success_metric": "99.9% uptime and positive user surveys.",
                        "acceptance_criteria": "Verify that feature runs successfully under default test conditions.",
                        "dependencies": [],
                        "risks": "Low"
                    })
                    
                pm_json = {
                    "Executive_Summary": intent.get("problem_statement", "An automated solution designed to solve key market workflow constraints."),
                    "Product_Vision": generated_vision,
                    "Problem_Statement": intent.get("problem_statement", "No explicit problem statement provided."),
                    "Goals_and_Objectives": ["Improve operational efficiency", "Minimize transaction latency", "Deliver premium user satisfaction"],
                    "Functional_Requirements": [
                        {
                            "id": "FR-001",
                            "title": "Administrative Console & Dashboard",
                            "description": "The system shall implement a web-based administrative console for visualization, management, and settings.",
                            "priority": "High",
                            "acceptance_criteria": ["The system displays all core telemetry fields on loading.", "Configuration updates are reflected within 5 seconds."],
                            "business_value": "Critical for direct administrative oversight.",
                            "user_persona": "PE-001",
                            "edge_cases": ["Loss of connectivity during update logs"],
                            "dependencies": []
                        }
                    ],
                    "Non_Functional_Requirements": {
                        "Performance": "Response latency under 200ms",
                        "Security": "TLS 1.3 encryption for data in transit",
                        "Scalability": "Support up to 10,000 concurrent active sessions"
                    },
                    "Core_Features": fallback_features,
                    "Assumptions": ["Target users have basic technical literacy."],
                    "Constraints": ["Must conform to standard data privacy rules."],
                    "Success_Metrics": ["System uptime > 99.9%", "User CSAT > 90%"],
                    "Open_Questions": ["Third-party API integration scope"]
                }
 
                
        # Validate critical keys
        profiler.start_sub("Validation Audits")
        required_keys = ["Executive_Summary", "Functional_Requirements", "Core_Features", "Success_Metrics"]
        for key in required_keys:
            if key not in pm_json:
                pm_json[key] = [] if key != "Executive_Summary" else "Unknown"
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
 
        log_entry = {
            "agent": "ProductManagerAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.90,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0.0",
        }
        
        # --- Validate canonical entities ---
        _log_entity_warnings(pm_json)
        profiler.end_sub("Validation Audits")
        
        profiler.start_sub("Formatting & Markdown")

        # 1. Executive Summary — handle both new dict format and legacy string
        exec_summary_raw = pm_json.get("Executive_Summary", "")
        if isinstance(exec_summary_raw, dict):
            es = exec_summary_raw
            exec_summary = (
                f"**Problem:** {es.get('problem', '')}\n\n"
                f"**Opportunity:** {es.get('opportunity', '')}\n\n"
                f"**Market:** {es.get('market', '')}\n\n"
                f"**Strategy:** {es.get('strategy', '')}\n\n"
                f"**KPIs:** {', '.join(es.get('kpis', []))}\n\n"
                f"**Timeline:** {es.get('timeline', '')}\n\n"
                f"**Risks:** {', '.join(es.get('risks', []) if isinstance(es.get('risks'), list) else [str(es.get('risks',''))])}\n\n"
                f"**Investment Summary:** {es.get('investment_summary', '')}"
            )
        elif isinstance(exec_summary_raw, list):
            exec_summary = "\n".join(f"- {item}" for item in exec_summary_raw)
        else:
            exec_summary = str(exec_summary_raw)
        # 2. User Personas — handle new canonical entity format
        personas_list = pm_json.get("User_Personas") or ba.get("user_personas") or ba.get("User Personas", [])
        personas_formatted = []
        for p in personas_list:
            if not isinstance(p, dict):
                personas_formatted.append(str(p))
                continue
            pname = p.get("name") or p.get("role") or "User Persona"
            prole = p.get("role") or "Persona Role"
            goals = p.get("goals") or [p.get("needs", "")]
            goals_str = ", ".join(goals) if isinstance(goals, list) else str(goals)
            pain = p.get("pain_points") or p.get("frustrations") or []
            pain_str = ", ".join(pain) if isinstance(pain, list) else str(pain)
            personas_formatted.append(
                f"**{pname}** ({p.get('id','')}) — {prole}\n"
                f"- *Goals:* {goals_str}\n"
                f"- *Frustrations:* {pain_str or 'Not specified'}\n"
                f"- *Motivations:* {p.get('motivations', 'Not specified')}\n"
                f"- *Technical Proficiency:* {p.get('technical_proficiency', 'Medium')}\n"
                f"- *Daily Workflow:* {p.get('daily_workflow') or p.get('workflow', 'Not specified')}"
            )
        personas_md = "\n\n".join(personas_formatted)
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

        # 5. High-Level Roadmap Formatting
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

        problem_statement = pm_json.get("Problem_Statement") or str(exec_summary_raw)
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
            prd_content["\u26a0\ufe0f Risk Factors"] = "See Risk Factors in the Executive Summary and individual Functional Requirements above."
 
        prd_content = {k: str(v) for k, v in prd_content.items() if v and (str(v).strip() if isinstance(v, str) else True)}
 
        res_ctx = context.clone(
            prd=pm_json,
            deliverables={
                "Product Requirements Document (PRD)": {
                    "content": prd_content,
                    "entities": {
                        "features": pm_json.get("Core_Features", []),
                        "functional_requirements": pm_json.get("Functional_Requirements", []),
                        "personas": pm_json.get("User_Personas", []),
                    },
                }
            }
        ).add_agent_log(log_entry)
        profiler.end_sub("Formatting & Markdown")
        return res_ctx

# Auto-register agent
registry.register("product_manager", ProductManagerAgent())


def _log_entity_warnings(pm_json: dict) -> None:
    """Emit warnings for any canonical entity violations in PM output."""
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    all_warnings = []
    for feat in pm_json.get("Core_Features", []):
        fid = feat.get("id", "FT-?")
        all_warnings.extend(validate_entity_envelope(feat, fid))
        all_warnings.extend(validate_domain_fields(feat, FEATURE_REQUIRED, fid))
    for fr in pm_json.get("Functional_Requirements", []):
        frid = fr.get("id", "FR-?")
        all_warnings.extend(validate_entity_envelope(fr, frid))
        all_warnings.extend(validate_domain_fields(fr, FUNCTIONAL_REQUIREMENT_REQUIRED, frid))
    if all_warnings:
        _logger.warning(
            f"ProductManagerAgent: {len(all_warnings)} entity warnings:\n"
            + "\n".join(f"  ⚠ {w}" for w in all_warnings)
        )


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
