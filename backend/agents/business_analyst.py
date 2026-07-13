import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import BUSINESS_ANALYST_SYSTEM_PROMPT
from backend.agents.entity_schema import (
    validate_entity_envelope, validate_domain_fields,
    BUSINESS_GOAL_REQUIRED, PERSONA_REQUIRED
)
from rag import retrieve_business

logger = logging.getLogger(__name__)


class BusinessAnalystAgent(BaseAgent):
    """Business Analyst Agent — produces canonical structured BA entities."""

    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing BusinessAnalystAgent...")
        start_time = time.perf_counter()
        
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()

        intent = context.intent_context
        problem = intent.get("problem_statement", "")
        features_list = intent.get("core_features", [])

        profiler.start_sub("RAG Loading & Search")
        retrieval_query = f"{problem} {' '.join(features_list)}".strip() or context.idea
        logger.info(f"Retrieving business KB context for query: '{retrieval_query[:50]}...'")
        context_docs = retrieve_business(retrieval_query, k=2)
        context_str = "\n\n".join([doc.page_content for doc in context_docs])
        logger.info(f"Retrieved {len(context_docs)} chunks from business index.")
        profiler.end_sub("RAG Loading & Search")

        profiler.start_sub("Prompt Construction")
        user_message = f"""RAG Context:
{context_str}

Intent Context (Canonical Source of Truth):
{json.dumps(intent, indent=2)}

Original Product Idea:
{context.idea}

Current UTC timestamp: {datetime.now(timezone.utc).isoformat()}
"""

        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", BUSINESS_ANALYST_SYSTEM_PROMPT),
            ("user", user_message)
        ]
        profiler.end_sub("Prompt Construction")

        profiler.start_sub("LLM Invocation")
        raw_text = ""
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            profiler.end_sub("LLM Invocation")
            
            profiler.start_sub("Response Parsing")
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            ba_json = json.loads(raw_text)
            profiler.end_sub("Response Parsing")
        except Exception as e:
            profiler.end_sub("LLM Invocation")
            profiler.end_sub("Response Parsing")
            logger.error(f"Business Analyst LLM invoke or parse failed: {e}")
            ba_json = _fallback_ba(intent)

        # --- Post-processing & validation ---
        profiler.start_sub("Validation Audits")
        ba_json = _normalise_ba(ba_json, intent)
        _log_entity_warnings(ba_json)
        profiler.end_sub("Validation Audits")

        profiler.start_sub("Formatting & Markdown")
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry = {
            "agent": "BusinessAnalystAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0.0",
        }

        res_ctx = context.clone(business_analysis=ba_json).add_agent_log(log_entry)
        profiler.end_sub("Formatting & Markdown")
        return res_ctx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fallback_ba(intent: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "problem_statement": {
            "id": "PS-001",
            "text": intent.get("problem_statement", "Unknown problem"),
            "version": "1.0",
            "status": "Active",
            "confidence": 0.60,
            "priority_score": 7,
            "risk_score": 5,
            "ownership": {"agent": "BusinessAnalystAgent", "created_at": now, "last_modified_by": "BusinessAnalystAgent"},
            "source_attribution": ["intent_context:problem_statement"],
            "traceability": {"addressed_by": ["BG-001"]},
            "relationships": [{"type": "addressed_by", "target_id": "BG-001"}],
        },
        "business_goals": [
            {
                "id": "BG-001",
                "goal": f"Establish core product functionality for {intent.get('project_name', 'the product')}.",
                "smart": {
                    "specific": "Deliver MVP feature set.",
                    "measurable": "User adoption metric to be defined post-launch.",
                    "achievable": "Scoped to MVP delivery.",
                    "relevant": "Directly solves the stated problem.",
                    "time_bound": "Q4 2026.",
                },
                "owner": "Head of Product",
                "kpi": "User adoption rate",
                "baseline": "0 users (pre-launch)",
                "target_value": "1,000 active users in first 90 days",
                "timeline": "Q4 2026",
                "version": "1.0",
                "status": "Active",
                "confidence": 0.60,
                "priority_score": 7,
                "risk_score": 4,
                "ownership": {"agent": "BusinessAnalystAgent", "created_at": now, "last_modified_by": "BusinessAnalystAgent"},
                "source_attribution": ["intent_context:business_objective"],
                "traceability": {"implements": ["PS-001"], "realized_by": []},
                "relationships": [{"type": "addresses", "target_id": "PS-001"}],
            }
        ],
        "user_personas": [
            {
                "id": "PE-001",
                "name": "Primary User",
                "role": "End user of the product.",
                "goals": ["Use the product effectively."],
                "frustrations": ["Lack of existing solutions."],
                "workflow": "Interacts with the product daily to achieve their goals.",
                "technical_proficiency": "Medium",
                "motivations": "Solving the stated problem efficiently.",
                "version": "1.0",
                "status": "Active",
                "confidence": 0.60,
                "priority_score": 6,
                "risk_score": 2,
                "ownership": {"agent": "BusinessAnalystAgent", "created_at": now, "last_modified_by": "BusinessAnalystAgent"},
                "source_attribution": ["intent_context:primary_users"],
                "traceability": {"owns": [], "featured_in": []},
                "relationships": [],
            }
        ],
    }


def _normalise_ba(ba_json: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures backwards compatibility and normalises canonical keys."""
    now = datetime.now(timezone.utc).isoformat()

    # --- Handle legacy flat-string format from old prompt ---
    if "Problem Statement" in ba_json and "problem_statement" not in ba_json:
        text = ba_json.get("Problem Statement", "")
        ba_json["problem_statement"] = {
            "id": "PS-001", "text": text, "version": "1.0", "status": "Active",
            "confidence": 0.70, "priority_score": 8, "risk_score": 4,
            "ownership": {"agent": "BusinessAnalystAgent", "created_at": now, "last_modified_by": "BusinessAnalystAgent"},
            "source_attribution": ["intent_context:problem_statement"],
            "traceability": {"addressed_by": ["BG-001"]},
            "relationships": [{"type": "addressed_by", "target_id": "BG-001"}],
        }

    if "Business Goals" in ba_json and "business_goals" not in ba_json:
        goals = ba_json.get("Business Goals", [])
        ba_json["business_goals"] = [
            {
                "id": f"BG-{str(i+1).zfill(3)}",
                "goal": g if isinstance(g, str) else g.get("goal", str(g)),
                "smart": {"specific": "", "measurable": "", "achievable": "", "relevant": "", "time_bound": ""},
                "owner": "Head of Product", "kpi": "TBD", "baseline": "TBD", "target_value": "TBD", "timeline": "Q4 2026",
                "version": "1.0", "status": "Active", "confidence": 0.70, "priority_score": 7, "risk_score": 3,
                "ownership": {"agent": "BusinessAnalystAgent", "created_at": now, "last_modified_by": "BusinessAnalystAgent"},
                "source_attribution": ["intent_context:business_objective"],
                "traceability": {"implements": ["PS-001"], "realized_by": []},
                "relationships": [{"type": "addresses", "target_id": "PS-001"}],
            }
            for i, g in enumerate(goals)
        ]

    if "User Personas" in ba_json and "user_personas" not in ba_json:
        personas = ba_json.get("User Personas", [])
        ba_json["user_personas"] = [
            {
                "id": f"PE-{str(i+1).zfill(3)}",
                "name": p.get("name", f"Persona {i+1}") if isinstance(p, dict) else str(p),
                "role": p.get("role", "") if isinstance(p, dict) else "",
                "goals": [p.get("needs", "")] if isinstance(p, dict) else [],
                "frustrations": [],
                "workflow": "",
                "technical_proficiency": "Medium",
                "motivations": "",
                "version": "1.0", "status": "Active", "confidence": 0.70, "priority_score": 6, "risk_score": 2,
                "ownership": {"agent": "BusinessAnalystAgent", "created_at": now, "last_modified_by": "BusinessAnalystAgent"},
                "source_attribution": ["intent_context:primary_users"],
                "traceability": {"owns": [], "featured_in": []},
                "relationships": [],
            }
            for i, p in enumerate(personas)
        ]

    # Ensure required top-level keys
    if "problem_statement" not in ba_json:
        ba_json.update(_fallback_ba(intent))
    if "business_goals" not in ba_json:
        ba_json["business_goals"] = _fallback_ba(intent)["business_goals"]
    if "user_personas" not in ba_json:
        ba_json["user_personas"] = _fallback_ba(intent)["user_personas"]

    # Populating legacy keys for complete backwards compatibility
    if "problem_statement" in ba_json and "Problem Statement" not in ba_json:
        ba_json["Problem Statement"] = ba_json["problem_statement"].get("text", "")
    if "business_goals" in ba_json and "Business Goals" not in ba_json:
        ba_json["Business Goals"] = [g.get("goal", "") for g in ba_json["business_goals"]]
    if "user_personas" in ba_json and "User Personas" not in ba_json:
        ba_json["User Personas"] = [
            {"name": p.get("name", ""), "role": p.get("role", ""), "needs": ", ".join(p.get("goals", []))}
            for p in ba_json["user_personas"]
        ]

    return ba_json


def _log_entity_warnings(ba_json: Dict[str, Any]) -> None:
    all_warnings = []
    ps = ba_json.get("problem_statement", {})
    all_warnings.extend(validate_entity_envelope(ps, "PS-001"))
    for goal in ba_json.get("business_goals", []):
        all_warnings.extend(validate_entity_envelope(goal, goal.get("id", "BG-?")))
        all_warnings.extend(validate_domain_fields(goal, BUSINESS_GOAL_REQUIRED, goal.get("id", "BG-?")))
    for persona in ba_json.get("user_personas", []):
        all_warnings.extend(validate_entity_envelope(persona, persona.get("id", "PE-?")))
        all_warnings.extend(validate_domain_fields(persona, PERSONA_REQUIRED, persona.get("id", "PE-?")))
    if all_warnings:
        logger.warning(f"BusinessAnalystAgent: {len(all_warnings)} entity warnings:\n" + "\n".join(f"  ⚠ {w}" for w in all_warnings))


# Auto-register agent
registry.register("business_analyst", BusinessAnalystAgent())


# -- Backwards Compatible Public Wrapper --
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
        idea = user_input.get("idea", "") if isinstance(user_input, dict) else str(user_input)
        ctx = WorkspaceContext(idea=idea)
        ctx.intent_context = {
            "project_name": "Legacy Project",
            "industry": {"value": user_input.get("industry", "Other") if isinstance(user_input, dict) else "Other"},
            "product_type": {"value": user_input.get("product_type", "SaaS Platform") if isinstance(user_input, dict) else "SaaS Platform"},
            "audience": {"value": user_input.get("audience", "B2C") if isinstance(user_input, dict) else "B2C"},
            "problem_statement": idea,
            "core_features": [],
        }
        result_context = registry.get("business_analyst").execute(ctx)
        return result_context.business_analysis
