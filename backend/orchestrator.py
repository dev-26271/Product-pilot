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
        
        # Format the structured Markdown response content matching UI consumers
        goals_markdown = "\n".join([f"- {goal}" for goal in business_analysis.get("Business Goals", [])])
        personas_markdown = "\n\n".join([
            f"**{p.get('name')} ({p.get('role')})**\n{p.get('needs')}"
            for p in business_analysis.get("User Personas", [])
        ])
        objectives_markdown = "\n".join([f"- {obj}" for obj in product_plan.get("Objectives", [])])
        features_markdown = "\n\n".join([
            f"**{f.get('name')} (Priority: {f.get('priority')})**\n{f.get('description')}"
            for f in product_plan.get("Features", [])
        ])
        nfr_markdown = "\n".join([f"- {r}" for r in product_plan.get("Non_Functional_Requirements", [])])
        metrics_markdown = "\n".join([f"- {m}" for m in product_plan.get("Success_Metrics", [])])
        acceptance_markdown = "\n".join([f"- {a}" for a in product_plan.get("Acceptance_Criteria", [])])
        
        prd_content = {
            "🎯 Problem Statement": business_analysis.get("Problem Statement", ""),
            "📈 Business Goals": goals_markdown,
            "👥 User Personas": personas_markdown,
            "🏹 Objectives": objectives_markdown,
            "✨ Core Features": features_markdown,
            "⚙️ Non-Functional Requirements": nfr_markdown,
            "📊 Success Metrics": metrics_markdown,
            "✅ Acceptance Criteria": acceptance_markdown
        }
        
        # Add risk analysis content if checked
        if project_data.get("risk_analysis", True):
            prd_content["⚠️ Risk Factors"] = (
                "Initial synchronization intervals and compatibility vectors during client updates."
            )
            
        # Build the workspace — only PRD is generated initially; all others are lazy
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
