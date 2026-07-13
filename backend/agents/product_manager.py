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
        context_docs = retrieve_product(retrieval_query, k=3)
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
        prd_content = {
            "📋 Executive Summary":        pm_json.get("Executive_Summary", ""),
            "🔭 Product Vision":            pm_json.get("Product_Vision", ""),
            "🎯 Problem Statement":         pm_json.get("Problem_Statement") or pm_json.get("Executive_Summary", ""),
            "👥 User Personas":             "\n\n".join([f"**{p.get('name')} ({p.get('role')})**\n{p.get('needs')}" for p in ba.get("User Personas", [])]),
            "📈 Goals & Objectives":        "\n".join([f"- {g}" for g in pm_json.get("Goals_and_Objectives", [])]),
            "⚙️ Functional Requirements":  "\n\n".join([f"**{r.get('id', '')} — {r.get('title', '')}** (Priority: {r.get('priority', '')})\n{r.get('description', '')}\n*Acceptance Criteria:* {r.get('acceptance_criteria', '')}" for r in pm_json.get("Functional_Requirements", [])]),
            "🔒 Non-Functional Requirements": "\n".join([f"**{k}:** {v}" for k, v in pm_json.get("Non_Functional_Requirements", {}).items()]) if isinstance(pm_json.get("Non_Functional_Requirements"), dict) else "",
            "✨ Core Features":             "\n\n".join([f"**{f.get('name', '')} (Priority: {f.get('priority', '')})**\n{f.get('description', '')}\n*Business Value:* {f.get('business_value', '')}" for f in pm_json.get("Core_Features", [])]),
            "💡 Assumptions":               "\n".join([f"- {a}" for a in pm_json.get("Assumptions", [])]),
            "🚧 Constraints":               "\n".join([f"- {c}" for c in pm_json.get("Constraints", [])]),
            "📊 Success Metrics":           "\n".join([f"- {m}" for m in pm_json.get("Success_Metrics", [])]),
            "❓ Open Questions":            "\n".join([f"- {q}" for q in pm_json.get("Open_Questions", [])])
        }
        
        if context.metadata.get("risk_analysis", True):
            prd_content["⚠️ Risk Factors"] = "Initial synchronization intervals and compatibility vectors during client updates."
            
        prd_content = {k: v for k, v in prd_content.items() if v and v.strip()}
        
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
