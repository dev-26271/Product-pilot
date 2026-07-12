import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.agents.business_analyst import generate_business_analysis
from backend.agents.product_manager import generate_product_requirements
from backend.api import create_project

logger = logging.getLogger(__name__)

class OrchestrationStrategy(ABC):
    """Abstract Strategy interface for routing the multi-agent pipeline execution."""
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the specific orchestration workflow logic."""
        pass

class PythonLocalStrategy(OrchestrationStrategy):
    """Runs the initial PRD-only pipeline locally using BA → PM agents.
    
    This strategy generates ONLY the PRD. All other documents (BRD, SRS,
    User Stories, Roadmap, Jira Tasks, Sprint Backlog) are generated lazily
    on demand via their specialized agents.
    """
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing PythonLocalStrategy (PRD-only initial generation)...")
        start_time = time.perf_counter()
        
        project_data = payload.get("project", payload)
        
        # Step 1: Run Business Analyst Agent
        ba_start = time.perf_counter()
        business_analysis = generate_business_analysis(project_data)
        ba_duration = time.perf_counter() - ba_start
        logger.info(f"Business Analyst Agent completed in {ba_duration:.4f} seconds.")
        
        # Step 2: Run Product Manager Agent to produce PRD content
        pm_start = time.perf_counter()
        product_plan = generate_product_requirements(business_analysis)
        pm_duration = time.perf_counter() - pm_start
        logger.info(f"Product Manager Agent completed in {pm_duration:.4f} seconds.")
        
        # ── Assemble the 11-section industry-standard PRD from PM agent output ──
        
        # 1. Executive Summary
        exec_summary = product_plan.get("Executive_Summary", "")
        
        # 2. Product Vision
        product_vision = product_plan.get("Product_Vision", "")
        
        # 3. Problem Statement (prefer PM's enriched version; fall back to BA's)
        problem_statement = product_plan.get("Problem_Statement") or business_analysis.get("Problem Statement", "")
        
        # 4. Goals & Objectives
        goals_list = business_analysis.get("Business Goals", [])
        objectives_list = product_plan.get("Goals_and_Objectives", [])
        goals_md = "\n".join([f"- {g}" for g in goals_list])
        objectives_md = "\n".join([f"- {o}" for o in objectives_list])
        goals_and_objectives_md = (goals_md + ("\n" if goals_md and objectives_md else "") + objectives_md).strip()
        
        # 5. Functional Requirements
        func_reqs = product_plan.get("Functional_Requirements", [])
        func_reqs_md = "\n\n".join([
            f"**{r.get('id', '')} — {r.get('title', '')}** (Priority: {r.get('priority', '')})\n"
            f"{r.get('description', '')}\n"
            f"*Acceptance Criteria:* {r.get('acceptance_criteria', '')}"
            for r in func_reqs
        ])
        
        # 6. Non-Functional Requirements (dict of categories)
        nfr = product_plan.get("Non_Functional_Requirements", {})
        if isinstance(nfr, dict):
            nfr_md = "\n".join([f"**{k}:** {v}" for k, v in nfr.items()])
        else:
            nfr_md = "\n".join([f"- {r}" for r in nfr])
        
        # 7. Core Features
        features = product_plan.get("Core_Features", [])
        features_md = "\n\n".join([
            f"**{f.get('name', '')} (Priority: {f.get('priority', '')})**\n"
            f"{f.get('description', '')}\n"
            f"*Business Value:* {f.get('business_value', '')}"
            for f in features
        ])
        
        # 8. Assumptions
        assumptions_md = "\n".join([f"- {a}" for a in product_plan.get("Assumptions", [])])
        
        # 9. Constraints
        constraints_md = "\n".join([f"- {c}" for c in product_plan.get("Constraints", [])])
        
        # 10. Success Metrics
        metrics_md = "\n".join([f"- {m}" for m in product_plan.get("Success_Metrics", [])])
        
        # 11. Open Questions
        questions_md = "\n".join([f"- {q}" for q in product_plan.get("Open_Questions", [])])
        
        # 12. User Personas (from BA)
        personas_md = "\n\n".join([
            f"**{p.get('name')} ({p.get('role')})**\n{p.get('needs')}"
            for p in business_analysis.get("User Personas", [])
        ])
        
        prd_content = {
            "📋 Executive Summary":        exec_summary,
            "🔭 Product Vision":            product_vision,
            "🎯 Problem Statement":         problem_statement,
            "👥 User Personas":             personas_md,
            "📈 Goals & Objectives":        goals_and_objectives_md,
            "⚙️ Functional Requirements":  func_reqs_md,
            "🔒 Non-Functional Requirements": nfr_md,
            "✨ Core Features":             features_md,
            "💡 Assumptions":               assumptions_md,
            "🚧 Constraints":               constraints_md,
            "📊 Success Metrics":           metrics_md,
            "❓ Open Questions":            questions_md,
        }
        
        # Remove blank sections to keep the UI clean
        prd_content = {k: v for k, v in prd_content.items() if v and v.strip()}
        
        # Add risk analysis if selected
        if project_data.get("risk_analysis", True):
            prd_content["⚠️ Risk Factors"] = (
                "Initial synchronization intervals and compatibility vectors during client updates."
            )
            
        # Build workspace — only PRD generated initially; all others are lazy
        deliverables = {
            "Product Requirements Document (PRD)": {"content": prd_content},
        }
        
        total_duration = time.perf_counter() - start_time
        logger.info(f"Initial PRD generation completed in {total_duration:.4f} seconds.")
        
        return {
            "success": True,
            "data": deliverables,
            "business_analysis": business_analysis
        }

class N8NWebhookStrategy(OrchestrationStrategy):
    """Dispatches the payload to the external n8n webhook orchestration service."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing N8NWebhookStrategy...")
        start_time = time.perf_counter()
        
        response = create_project(payload)
        
        duration = time.perf_counter() - start_time
        logger.info(f"N8N Webhook orchestration pipeline completed in {duration:.4f} seconds.")
        return response

def generate_prd(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolves the configured strategy and executes the PRD-only initial generation.
    
    This function generates ONLY the PRD as the workspace foundation.
    No other documents are generated here. They are produced lazily
    by their specialized agents when the user explicitly requests them.
    
    Strategy Selection Priority:
    1. User selection passed in payload (e.g. payload["mode"])
    2. Environment variable 'USE_N8N'
    3. Default to Python
    
    Args:
        payload (dict): The project payload.
        
    Returns:
        dict: The generation outcome containing PRD deliverables and business_analysis.
    """
    mode = payload.get("mode")
    if not mode:
        env_val = os.getenv("USE_N8N", "").lower()
        if env_val in ("true", "1", "yes"):
            mode = "n8n"
        else:
            mode = "python"
            
    logger.info(f"Resolved orchestration mode: '{mode}'")
    
    if mode == "n8n":
        strategy = N8NWebhookStrategy()
    else:
        strategy = PythonLocalStrategy()
        
    try:
        return strategy.execute(payload)
    except Exception as e:
        logger.error(f"Orchestration execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
