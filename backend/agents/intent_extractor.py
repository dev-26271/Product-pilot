import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import INTENT_EXTRACTOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class IntentExtractorAgent(BaseAgent):
    """Agent that extracts structured intent and classifications from a raw idea."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing IntentExtractorAgent...")
        start_time = time.perf_counter()
        
        # Pull pre-parsed metadata passed as kwargs (if any) to guide the LLM
        pre_parsed = kwargs.get("pre_parsed_metadata", {})
        
        user_message = f"""Product Idea: {context.idea}

Pre-parsed Metadata (if any):
- Industry: {pre_parsed.get('industry', 'Unknown')}
- Product Type: {pre_parsed.get('product_type', 'Unknown')}
- Audience: {pre_parsed.get('audience', 'Unknown')}
"""
        
        messages = [
            ("system", INTENT_EXTRACTOR_SYSTEM_PROMPT),
            ("user", user_message)
        ]
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        
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
                
            intent_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Intent Extraction LLM invoke or parse failed: {e}")
            # Sensible fallback JSON
            intent_json = {
                "project_name": "Product Project",
                "industry": {"value": pre_parsed.get("industry", "Other"), "confidence": 0.5},
                "product_type": {"value": pre_parsed.get("product_type", "SaaS Platform"), "confidence": 0.5},
                "audience": {"value": pre_parsed.get("audience", "B2C"), "confidence": 0.5},
                "primary_users": [],
                "problem_statement": "Unknown",
                "business_objective": "Unknown",
                "core_features": [],
                "constraints": [],
                "assumptions": [],
                "success_metrics": [],
                "technology_hints": [],
                "keywords": [],
                "risks": [],
                "unknowns": []
            }
            
        # Ensure all required fields exist
        required_keys = [
            "project_name", "industry", "product_type", "audience", "primary_users",
            "problem_statement", "business_objective", "core_features", "constraints",
            "assumptions", "success_metrics", "technology_hints", "keywords", "risks", "unknowns"
        ]
        for key in required_keys:
            if key not in intent_json:
                intent_json[key] = "Unknown" if key in ["project_name", "problem_statement", "business_objective"] else []
                
        # Calculate scores and construct the metadata overrides if not present
        industry_meta = intent_json.get("industry", {})
        if not isinstance(industry_meta, dict):
            intent_json["industry"] = {"value": industry_meta, "confidence": 0.9}
        product_meta = intent_json.get("product_type", {})
        if not isinstance(product_meta, dict):
            intent_json["product_type"] = {"value": product_meta, "confidence": 0.9}
        audience_meta = intent_json.get("audience", {})
        if not isinstance(audience_meta, dict):
            intent_json["audience"] = {"value": audience_meta, "confidence": 0.9}

        # Respect manual UI selection if passed in kwargs
        if pre_parsed.get("industry") and pre_parsed["industry"] != "Auto Detect":
            intent_json["industry"] = {"value": pre_parsed["industry"], "confidence": 1.0}
        if pre_parsed.get("product_type") and pre_parsed["product_type"] != "Auto Detect":
            intent_json["product_type"] = {"value": pre_parsed["product_type"], "confidence": 1.0}
        if pre_parsed.get("audience") and pre_parsed["audience"] != "Auto Detect":
            intent_json["audience"] = {"value": pre_parsed["audience"], "confidence": 1.0}

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Update metadata dict inside context
        new_metadata = context.metadata.copy()
        new_metadata.update({
            "name": intent_json["project_name"],
            "industry": intent_json["industry"]["value"],
            "industry_confidence": intent_json["industry"]["confidence"],
            "product_type": intent_json["product_type"]["value"],
            "product_type_confidence": intent_json["product_type"]["confidence"],
            "audience": intent_json["audience"]["value"],
            "audience_confidence": intent_json["audience"]["confidence"],
        })
        
        # Log entry
        log_entry = {
            "agent": "IntentExtractorAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": intent_json["industry"]["confidence"],
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        # Return new cloned context
        return context.clone(
            intent_context=intent_json,
            metadata=new_metadata
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("intent_extractor", IntentExtractorAgent())
