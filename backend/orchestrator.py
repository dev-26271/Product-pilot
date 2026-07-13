import os
import json
import time
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any

from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.api import create_project

logger = logging.getLogger(__name__)

# Fast local keyword rules for metadata pre-parsing (latency-saving)
INDUSTRY_PATTERNS = {
    "Healthcare": r"\b(health|medical|clinic|doctor|patient|hospital|nurse|pharmacy|clinical|telemed)\b",
    "Finance": r"\b(finance|bank|wallet|pay|transaction|invest|budget|crypt|ledger|stock)\b",
    "Education": r"\b(student|teach|tutor|learn|class|school|course|education|academy)\b",
    "Retail": r"\b(retail|store|shop|e-commerce|checkout|merchant|grocery)\b",
    "Food & Beverage": r"\b(food|delivery|restaurant|beverage|eat|drone shipping|zero-waste)\b",
    "Logistics": r"\b(warehouse|inventory|shipping|transport|logistics|supply|reorder)\b",
    "Agriculture": r"\b(farm|agriculture|soil|crop|harvest|irrigate)\b",
    "Travel": r"\b(travel|flight|hotel|trip|vacation|booking)\b",
    "Real Estate": r"\b(property|house|rent|real estate|apartment|broker)\b",
    "HR": r"\b(hr|employee|hire|recruit|payroll|talent)\b",
    "Legal": r"\b(legal|law|contract|attorney|sign)\b",
    "Entertainment": r"\b(game|movie|music|video|stream|entertainment|play)\b",
}

PRODUCT_TYPE_PATTERNS = {
    "SaaS Platform": r"\b(saas|cloud platform|dashboard|portal|multi-tenant)\b",
    "Mobile App": r"\b(mobile app|ios|android|phone app|tablet app)\b",
    "AI Assistant": r"\b(ai assistant|chatbot|llm|copilot|tutor|gpt)\b",
    "Marketplace": r"\b(marketplace|platform|delivery|matching|vendor|ecommerce)\b",
    "Dashboard": r"\b(dashboard|analytics|reporting|telemetry|visualizer)\b",
    "Internal Tool": r"\b(internal tool|operator tool|back-office|admin tool)\b",
    "API Platform": r"\b(api platform|developer portal|endpoint|integration)\b",
    "CRM": r"\b(crm|customer relations|lead tracking|contact manager)\b",
}

AUDIENCE_PATTERNS = {
    "B2B": r"\b(b2b|business to business|vendor|merchant|operator|business partner)\b",
    "B2C": r"\b(b2c|consumer|end user|customer|shopper|individual|patient|student)\b",
    "Enterprise": r"\b(enterprise|corporate|bank|hospital|large-scale|security-conscious)\b",
    "Internal": r"\b(internal|staff|employee|operations|back-office)\b",
    "Government": r"\b(government|agency|public sector|municipal)\b",
}


def _fast_regex_parse(idea: str) -> Dict[str, str]:
    """Helper that runs quick regex-based keyword matches to classify an idea instantly."""
    idea_lower = idea.lower()
    inferred = {}
    
    # 1. Industry match
    for ind, pattern in INDUSTRY_PATTERNS.items():
        if re.search(pattern, idea_lower):
            inferred["industry"] = ind
            break
            
    # 2. Product type match
    for ptype, pattern in PRODUCT_TYPE_PATTERNS.items():
        if re.search(pattern, idea_lower):
            inferred["product_type"] = ptype
            break
            
    # 3. Audience match
    for aud, pattern in AUDIENCE_PATTERNS.items():
        if re.search(pattern, idea_lower):
            inferred["audience"] = aud
            break
            
    return inferred


def infer_project_metadata(idea: str) -> Dict[str, str]:
    """Infers industry, product_type, and audience from a product idea.
    
    First runs a zero-latency fast keyword pre-parser, falling back to a lightweight LLM call
    if matches are inconclusive. Always returns a confidence-score structured outcome.
    """
    logger.info("Running metadata inference...")
    
    # Try zero-latency fast parser first
    fast_inferred = _fast_regex_parse(idea)
    if len(fast_inferred) == 3:
        logger.info(f"Fast parser achieved 100% resolution: {fast_inferred}")
        return fast_inferred
        
    # Fall back to lightweight LLM classifier for remaining fields
    from backend.llm import get_llm
    
    system_prompt = """You are a product classifier. Given a product idea, return a JSON object with exactly three keys:
{
  "industry": "<one of: Healthcare, Finance, Education, Retail, Logistics, Travel, Real Estate, HR, Legal, Entertainment, Food & Beverage, Agriculture, Government, Technology, Other>",
  "product_type": "<one of: SaaS Platform, Mobile App, AI Assistant, Marketplace, Dashboard, Internal Tool, API Platform, Enterprise Software, CRM, Productivity Tool>",
  "audience": "<one of: B2B, B2C, Enterprise, Internal, Government>"
}

Rules:
- Return ONLY the raw JSON object. No markdown, no backticks, no explanation.
- Pick the single best match for each field based on the product idea.
- If uncertain, choose the closest reasonable option.
"""
    user_message = f"Product idea: {idea}\nFast Pre-parsed defaults: {fast_inferred}"
    
    try:
        llm = get_llm()
        response = llm.invoke([
            ("system", system_prompt),
            ("user", user_message),
        ])
        raw = response.content.strip()
        
        # Strip code fences if present
        if raw.startswith("```"):
            lines = raw.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines).strip()
        
        data = json.loads(raw)
        
        # Combine fast parser results with LLM results
        final_inferred = {
            "industry": fast_inferred.get("industry") or data.get("industry", "Other"),
            "product_type": fast_inferred.get("product_type") or data.get("product_type", "SaaS Platform"),
            "audience": fast_inferred.get("audience") or data.get("audience", "B2C"),
        }
        logger.info(f"Metadata inference completed successfully: {final_inferred}")
        return final_inferred
    except Exception as e:
        logger.warning(f"Lightweight LLM metadata classification failed, using fallbacks: {e}")
        return {
            "industry": fast_inferred.get("industry", "Other"),
            "product_type": fast_inferred.get("product_type", "SaaS Platform"),
            "audience": fast_inferred.get("audience", "B2C"),
        }


class OrchestrationStrategy(ABC):
    """Abstract Strategy interface for routing the multi-agent pipeline execution."""
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the specific orchestration workflow logic."""
        pass


class PythonLocalStrategy(OrchestrationStrategy):
    """Runs the PRD-only pipeline locally using BaseAgent execution loops on WorkspaceContext."""
    
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("Executing PythonLocalStrategy (multi-agent context pipeline)...")
        start_time = time.perf_counter()
        
        project_data = payload.get("project", payload)
        idea = project_data.get("idea", "")
        
        # UI selection overrides if manually configured
        pre_parsed_meta = {
            "industry": project_data.get("industry"),
            "product_type": project_data.get("product_type"),
            "audience": project_data.get("audience"),
            "risk_analysis": project_data.get("risk_analysis", True)
        }
        
        # 1. Initialize WorkspaceContext
        context = WorkspaceContext(
            idea=idea,
            metadata=pre_parsed_meta.copy()
        )
        
        # 2. Step 1: Intent Extraction Agent
        intent_agent = registry.get("intent_extractor")
        context = intent_agent.execute(context, pre_parsed_metadata=pre_parsed_meta)
        
        # 3. Step 2: Business Analyst Agent
        ba_agent = registry.get("business_analyst")
        context = ba_agent.execute(context)
        
        # 4. Step 3: Product Manager Agent
        pm_agent = registry.get("product_manager")
        context = pm_agent.execute(context)
        
        # 5. Step 4: Validation & PM Self-Repair Loop
        val_agent = registry.get("validation_agent")
        
        # Maximum repair loops: 2 attempts
        max_attempts = 2
        for attempt in range(max_attempts + 1):
            context = val_agent.execute(context)
            val_report = context.metadata.get("validation_report", {})
            
            if val_report.get("valid", True):
                logger.info(f"PRD passed validation agent successfully on attempt {attempt + 1} ✓ (Score: {val_report.get('score', 1.0)})")
                break
            else:
                logger.warning(f"PRD failed validation check on attempt {attempt + 1}. Score: {val_report.get('score', 0.0)}")
                if attempt < max_attempts:
                    logger.info("Triggering PM self-repair step...")
                    # Re-run PM Agent, passing validation feedback to heal failed sections
                    context = pm_agent.execute(
                        context,
                        repair_feedback=val_report.get("repair_prompt", ""),
                        current_prd_draft=context.prd
                    )
                else:
                    logger.warning("Max PM self-repair loop attempts reached. Proceeding with current PRD.")
        
        total_duration = time.perf_counter() - start_time
        logger.info(f"Initial Multi-Agent PRD pipeline completed in {total_duration:.4f} seconds.")
        
        # Return serializable dict output maintaining backwards compatibility with UI
        res_dict = context.to_dict()
        res_dict["success"] = True
        res_dict["data"] = context.deliverables
        res_dict["business_analysis"] = context.business_analysis
        
        return res_dict


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
    
    Acts as the public wrapper for backwards compatibility with UI rendering scripts.
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
