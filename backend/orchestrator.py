import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.agents.business_analyst import generate_business_analysis
from backend.agents.product_manager import generate_product_plan
from backend.api import create_project

logger = logging.getLogger(__name__)

class OrchestrationStrategy(ABC):
    """Abstract Strategy interface for routing the multi-agent pipeline execution."""
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the specific orchestration workflow logic."""
        pass

class PythonLocalStrategy(OrchestrationStrategy):
    """Runs the complete multi-agent pipeline locally on python using local agent modules."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing PythonLocalStrategy...")
        start_time = time.perf_counter()
        
        project_data = payload.get("project", payload)
        deliverable = project_data.get("deliverable", "Product Requirements Document (PRD)")
        
        # Step 1: Run Business Analyst Agent
        ba_start = time.perf_counter()
        business_analysis = generate_business_analysis(project_data)
        ba_duration = time.perf_counter() - ba_start
        logger.info(f"Business Analyst Agent completed in {ba_duration:.4f} seconds.")
        
        # Step 2: Run Product Manager Agent
        pm_start = time.perf_counter()
        product_plan = generate_product_plan(project_data, business_analysis)
        pm_duration = time.perf_counter() - pm_start
        logger.info(f"Product Manager Agent completed in {pm_duration:.4f} seconds.")
        
        # Format the structured Markdown response content matching UI consumers
        goals_markdown = "\n".join([f"- {goal}" for goal in business_analysis.get("Business Goals", [])])
        personas_markdown = "\n\n".join([
            f"**{p.get('name')} ({p.get('role')})**\n{p.get('needs')}"
            for p in business_analysis.get("User Personas", [])
        ])
        features_markdown = "\n\n".join([
            f"**{f.get('name')} (Priority: {f.get('priority')})**\n{f.get('description')}"
            for f in product_plan.get("Features", [])
        ])
        roadmap_markdown = "\n\n".join([
            f"**{r.get('phase')}**\n{r.get('scope')}"
            for r in product_plan.get("Roadmap", [])
        ])
        
        deliverables_dict = {
            "Product Requirements Document (PRD)": {
                "content": {
                    "🎯 Problem Statement": business_analysis.get("Problem Statement", ""),
                    "📈 Business Goals": goals_markdown,
                    "👥 User Personas": personas_markdown,
                    "✨ Features": features_markdown,
                    "🗓️ Product Roadmap": roadmap_markdown
                }
            }
        }
        
        # Add risk analysis content if checked
        if project_data.get("risk_analysis", True):
            deliverables_dict["Product Requirements Document (PRD)"]["content"]["⚠️ Risk Factors"] = (
                "Initial synchronization intervals and compatibility vectors during client updates."
            )
            
        total_duration = time.perf_counter() - start_time
        logger.info(f"Local Python orchestration pipeline completed in {total_duration:.4f} seconds.")
        
        return {
            "success": True,
            "data": deliverables_dict
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
    """Resolves the configured strategy and executes the PRD orchestration pipeline.
    
    Strategy Selection Priority:
    1. User selection passed in payload (e.g. payload["mode"])
    2. Environment variable 'USE_N8N'
    3. Default to Python
    
    Args:
        payload (dict): The project payload.
        
    Returns:
        dict: The generation outcome.
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
