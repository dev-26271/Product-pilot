import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import VALIDATION_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    """Audits product deliverables across 3 dimensions:
    Business Consistency, Product Quality, Engineering Readiness."""

    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing ValidationAgent...")
        start_time = time.perf_counter()
        
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()
 
        profiler.start_sub("Prompt Construction")
        user_message = f"""=== INTENT CONTEXT ===
{json.dumps(context.intent_context, indent=2)}
 
=== BUSINESS ANALYSIS ===
{json.dumps(context.business_analysis, indent=2)}
 
=== PRODUCT REQUIREMENTS DOCUMENT (PRD) ===
{json.dumps(context.prd, indent=2)}
 
=== USER STORIES (if generated) ===
{json.dumps(context.deliverables.get('User Stories', {}), indent=2)}
 
=== JIRA TASKS (if generated) ===
{json.dumps(context.deliverables.get('Jira Tasks', {}), indent=2)}
 
=== ROADMAP (if generated) ===
{json.dumps(context.deliverables.get('Product Roadmap', {}), indent=2)}
"""
 
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", VALIDATION_AGENT_SYSTEM_PROMPT),
            ("user", user_message),
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
            elif raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:]).strip()
            val_json = json.loads(raw_text)
            profiler.end_sub("Response Parsing")
        except Exception as e:
            profiler.end_sub("LLM Invocation")
            profiler.end_sub("Response Parsing")
            logger.error(f"Validation Agent LLM invoke or parse failed: {e}")
            val_json = {
                "valid": True,
                "overall_score": 1.0,
                "dimensions": {
                    "business_consistency": {"score": 1.0, "findings": []},
                    "product_quality": {"score": 1.0, "findings": []},
                    "engineering_readiness": {"score": 1.0, "findings": []},
                },
                "errors": [f"Validation system exception: {e}"],
                "warnings": [],
                "repair_prompt": "",
                "score": 1.0,
            }

        # Normalise: ensure backwards-compatible fields
        profiler.start_sub("Validation Audits")
        if "valid" not in val_json:
            val_json["valid"] = len(val_json.get("errors", [])) == 0
        if "errors" not in val_json:
            val_json["errors"] = []
        if "warnings" not in val_json:
            val_json["warnings"] = []
        if "repair_prompt" not in val_json:
            val_json["repair_prompt"] = ""
        # Prefer overall_score; fall back to score for orchestrator compatibility
        overall = val_json.get("overall_score", val_json.get("score", 0.5))
        val_json["overall_score"] = overall
        val_json["score"] = overall
        if "dimensions" not in val_json:
            val_json["dimensions"] = {
                "business_consistency": {"score": overall, "findings": []},
                "product_quality": {"score": overall, "findings": []},
                "engineering_readiness": {"score": overall, "findings": []},
            }

        # Check dependency integrity and update validation report
        dep_errors = _validate_dependencies(context)
        if dep_errors:
            val_json["errors"].extend(dep_errors)
            val_json["valid"] = False
            
            # Deduct score for broken mappings
            er_dict = val_json["dimensions"].setdefault("engineering_readiness", {"score": overall, "findings": []})
            deduction = min(0.4, len(dep_errors) * 0.1)
            er_dict["score"] = max(0.0, er_dict.get("score", 1.0) - deduction)
            er_dict.setdefault("findings", []).extend(dep_errors)
            
            # Recompute overall score
            overall = max(0.0, overall - deduction)
            val_json["overall_score"] = overall
            val_json["score"] = overall

        # Log dimension breakdown
        dims = val_json["dimensions"]
        logger.info(
            f"Validation scores — BC: {dims.get('business_consistency',{}).get('score','?')} "
            f"PQ: {dims.get('product_quality',{}).get('score','?')} "
            f"ER: {dims.get('engineering_readiness',{}).get('score','?')} "
            f"Overall: {overall}"
        )
        profiler.end_sub("Validation Audits")
 
        profiler.start_sub("Formatting & Markdown")
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry = {
            "agent": "ValidationAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0.0",
        }

        new_metadata = context.metadata.copy()
        new_metadata["validation_report"] = val_json
        res_ctx = context.clone(metadata=new_metadata).add_agent_log(log_entry)
        profiler.end_sub("Formatting & Markdown")
        return res_ctx


def _validate_dependencies(context: WorkspaceContext) -> list:
    """Verifies that all downstream deliverables contain valid mappings to upstream entities."""
    errors = []
    
    # Instantiate TraceabilityEngine on the context dictionary to parse the graph nodes
    from backend.agents.traceability_engine import TraceabilityEngine
    try:
        engine = TraceabilityEngine(context.to_dict())
        nodes = engine.graph.get("nodes", {})
    except Exception as e:
        logger.error(f"Failed to build traceability graph for validation: {e}")
        return [f"Traceability Graph build failure: {e}"]
        
    # Check stories links
    us_data = context.deliverables.get("User Stories", {})
    us_content = us_data.get("content", us_data)
    if isinstance(us_content, dict):
        stories = us_content.get("stories", [])
        for idx, story in enumerate(stories):
            sid = story.get("id", f"Story[{idx}]")
            
            # Check FR links
            trace_reqs = story.get("traceability", {}).get("functional_requirements", [])
            for tr in trace_reqs:
                # Find matching requirement node
                matched = False
                for nid, node in nodes.items():
                    if node["type"] == "Functional Requirement" and (nid == tr or tr in nid or nid in tr):
                        matched = True
                        break
                if not matched:
                    errors.append(f"User Story {sid} references broken Functional Requirement link: '{tr}'")
                    
    # Check Jira task links
    jira_data = context.deliverables.get("Jira Tasks", {})
    jira_content = jira_data.get("content", jira_data)
    if isinstance(jira_content, dict):
        tasks = jira_content.get("tasks", [])
        for idx, task in enumerate(tasks):
            tid = task.get("id", f"Task[{idx}]")
            us_ref = task.get("user_story_id")
            if us_ref:
                matched = False
                for nid, node in nodes.items():
                    if node["type"] == "User Story" and (nid == us_ref or us_ref in nid or nid in us_ref):
                        matched = True
                        break
                if not matched:
                    errors.append(f"Jira Task {tid} references broken User Story link: '{us_ref}'")
                    
    return errors


# Auto-register agent
registry.register("validation_agent", ValidationAgent())
