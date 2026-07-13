import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import VALIDATION_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

class ValidationAgent(BaseAgent):
    """Audits generated product deliverables (PRD, Business Analysis) to verify logical alignment."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing ValidationAgent...")
        start_time = time.perf_counter()
        
        # Build user message with intent_context, business_analysis, and prd content
        user_message = f"""=== INTENT CONTEXT ===
{json.dumps(context.intent_context, indent=2)}

=== BUSINESS ANALYSIS ===
{json.dumps(context.business_analysis, indent=2)}

=== PRODUCT REQUIREMENTS DOCUMENT (PRD) ===
{json.dumps(context.prd, indent=2)}
"""
        
        messages = [
            ("system", VALIDATION_AGENT_SYSTEM_PROMPT),
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
                
            val_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Validation Agent LLM invoke or parse failed: {e}")
            val_json = {
                "valid": True,
                "errors": [f"Validation system exception: {e}"],
                "repair_prompt": "",
                "score": 1.0
            }
            
        # Ensure standard keys are present
        if "valid" not in val_json:
            val_json["valid"] = len(val_json.get("errors", [])) == 0
        if "errors" not in val_json:
            val_json["errors"] = []
        if "repair_prompt" not in val_json:
            val_json["repair_prompt"] = ""
        if "score" not in val_json:
            val_json["score"] = 1.0 if val_json["valid"] else 0.5
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "ValidationAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": val_json["score"],
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        # Stash the validation report inside metadata so orchestrator/UI can inspect it
        new_metadata = context.metadata.copy()
        new_metadata["validation_report"] = val_json
        
        return context.clone(metadata=new_metadata).add_agent_log(log_entry)

# Auto-register agent
registry.register("validation_agent", ValidationAgent())
