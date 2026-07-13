import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import BUSINESS_ANALYST_SYSTEM_PROMPT
from rag import retrieve_business

logger = logging.getLogger(__name__)

class BusinessAnalystAgent(BaseAgent):
    """Business Analyst Agent that processes the intent context to build structural business goals and user personas."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing BusinessAnalystAgent...")
        start_time = time.perf_counter()
        
        # Step 1: Extract intent details to build retrieval query
        intent = context.intent_context
        problem = intent.get("problem_statement", "")
        features_list = intent.get("core_features", [])
        
        # Retrieve context from RAG business index
        retrieval_query = f"{problem} {' '.join(features_list)}".strip() or context.idea
        logger.info(f"Retrieving business KB context for query: '{retrieval_query[:50]}...'")
        
        context_docs = retrieve_business(retrieval_query, k=2)
        context_str = "\n\n".join([doc.page_content for doc in context_docs])
        logger.info(f"Retrieved {len(context_docs)} chunks from business index.")
        
        # Step 2: Build final user prompt
        user_message = f"""RAG Context:
{context_str}

Intent Context (Canonical Source of Truth):
{json.dumps(intent, indent=2)}

Original Product Idea:
{context.idea}
"""
        
        # Step 3: Invoke LLM
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", BUSINESS_ANALYST_SYSTEM_PROMPT),
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
                
            ba_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Business Analyst LLM invoke or parse failed: {e}")
            ba_json = {
                "Problem Statement": problem or "Unknown",
                "Business Goals": [f"Establish initial goals for {intent.get('project_name', 'project')}"],
                "User Personas": [{"name": "Default Persona", "role": "End User", "needs": "Clean product delivery"}]
            }
            
        # Validate critical keys
        required_keys = ["Problem Statement", "Business Goals", "User Personas"]
        for key in required_keys:
            if key not in ba_json:
                ba_json[key] = [] if key != "Problem Statement" else "Unknown"
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "BusinessAnalystAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        return context.clone(
            business_analysis=ba_json
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("business_analyst", BusinessAnalystAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_business_analysis(user_input: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the orchestrator & tests."""
    if isinstance(user_input, WorkspaceContext):
        result_context = registry.get("business_analyst").execute(user_input)
        return result_context.business_analysis
    elif isinstance(user_input, dict) and "intent_context" in user_input:
        ctx = WorkspaceContext.from_dict(user_input)
        result_context = registry.get("business_analyst").execute(ctx)
        return result_context.business_analysis
    else:
        # Legacy direct payload format
        idea = user_input.get("idea", "") if isinstance(user_input, dict) else str(user_input)
        ctx = WorkspaceContext(idea=idea)
        # Populate a minimal intent context for BA execution
        ctx.intent_context = {
            "project_name": "Legacy Project",
            "industry": {"value": user_input.get("industry", "Other") if isinstance(user_input, dict) else "Other"},
            "product_type": {"value": user_input.get("product_type", "SaaS Platform") if isinstance(user_input, dict) else "SaaS Platform"},
            "audience": {"value": user_input.get("audience", "B2C") if isinstance(user_input, dict) else "B2C"},
            "problem_statement": idea,
            "core_features": []
        }
        result_context = registry.get("business_analyst").execute(ctx)
        return result_context.business_analysis
