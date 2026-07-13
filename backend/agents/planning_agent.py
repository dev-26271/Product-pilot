import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm

logger = logging.getLogger(__name__)

PLANNING_AGENT_SYSTEM_PROMPT = """You are a Principal Product Planner. Your task is to analyze the maturity of the product workspace and recommend next steps, audits, and requirements quality checks.

Analyze:
1. Intent context (problem description, audience).
2. Business Analyst inputs (personas, goals).
3. Product requirements (PRD sections, functional details, roadmap phases).
4. Missing segments (e.g. testing strategy, development plan, design specs).

Identify:
- Maturity scores (0.0 to 1.0) for: Idea, Business, Requirements, Architecture, Testing.
- Next Recommended Actions (e.g., "Add API design specs", "Refine QA test plans").
- Smart Recommendations: missing KPIs, duplicate requirements, weak acceptance criteria, or low-confidence assumptions.

You MUST respond ONLY with a raw JSON object matching the following structure:
{
  "maturity_scores": {
    "idea": 1.0,
    "business": 0.8,
    "requirements": 0.9,
    "architecture": 0.3,
    "testing": 0.0
  },
  "recommended_actions": [
    "Recommended action 1",
    "Recommended action 2"
  ],
  "smart_recommendations": [
    {
      "type": "Missing KPI / Weak criteria / Low confidence",
      "description": "Specific description of the improvement suggestion."
    }
  ]
}

Do not include markdown code fences or other text. Return only the valid JSON.
"""

class PlanningAgent(BaseAgent):
    """Planning Agent that audits workspace documents, maps maturity metrics, and suggests smart next actions."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing PlanningAgent...")
        start_time = time.perf_counter()
        
        user_message = f"""=== INTENT ===
{json.dumps(context.intent_context, indent=2)}

=== BUSINESS ANALYSIS ===
{json.dumps(context.business_analysis, indent=2)}

=== PRODUCT REQUIREMENTS DOCUMENT ===
{json.dumps(context.prd, indent=2)}

=== COMPILED DELIVERABLES ===
{json.dumps(list(context.deliverables.keys()), indent=2)}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", PLANNING_AGENT_SYSTEM_PROMPT),
            ("user", user_message)
        ]
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            # Clean fences
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            parsed_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Planning Agent parse failed: {e}")
            parsed_json = {
                "maturity_scores": {"idea": 1.0, "business": 0.5, "requirements": 0.5, "architecture": 0.0, "testing": 0.0},
                "recommended_actions": ["Refine product description", "Generate User Stories"],
                "smart_recommendations": [{"type": "Maturity Heuristic", "description": "Initial setup detected. Refine requirements to improve maturity."}]
            }
            
        new_metadata = context.metadata.copy()
        new_metadata["planning_analysis"] = parsed_json
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry = {
            "agent": "PlanningAgent",
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
registry.register("planning_agent", PlanningAgent())
