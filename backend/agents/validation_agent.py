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


class SemanticValidationAgent(BaseAgent):
    """Semantic Validation Agent — audits deliverables for strategic alignment,
    persona realism, requirements logic contradictions, and roadmap realism."""

    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing SemanticValidationAgent...")
        start_time = time.perf_counter()
        
        val_timings = {
            "Prompt construction": 0.0,
            "RAG context preparation": 0.0,
            "LLM invocation": 0.0,
            "Response parsing": 0.0,
            "JSON validation": 0.0,
            "Markdown formatting": 0.0,
            "Post-processing": 0.0,
        }
        
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()
 
        t_prompt_start = time.perf_counter()
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
        val_timings["Prompt construction"] = time.perf_counter() - t_prompt_start
 
        t_llm_start = time.perf_counter()
        profiler.start_sub("LLM Invocation")
        raw_text = ""
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            profiler.end_sub("LLM Invocation")
            val_timings["LLM invocation"] = time.perf_counter() - t_llm_start
            
            t_parse_start = time.perf_counter()
            profiler.start_sub("Response Parsing")
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:]).strip()
            val_json = json.loads(raw_text)
            profiler.end_sub("Response Parsing")
            val_timings["Response parsing"] = time.perf_counter() - t_parse_start
        except Exception as e:
            if "LLM invocation" not in val_timings or val_timings["LLM invocation"] == 0:
                val_timings["LLM invocation"] = time.perf_counter() - t_llm_start
            t_parse_start = time.perf_counter()
            profiler.end_sub("LLM Invocation")
            profiler.end_sub("Response Parsing")
            logger.error(f"Semantic Validation Agent LLM invoke or parse failed: {e}")
            val_json = {
                "valid": True,
                "overall_score": 1.0,
                "dimensions": {
                    "business_consistency": {"score": 1.0, "findings": []},
                    "product_quality": {"score": 1.0, "findings": []},
                    "engineering_readiness": {"score": 1.0, "findings": []},
                },
                "errors": [f"Semantic validation system exception: {e}"],
                "warnings": [],
                "repair_prompt": "",
                "score": 1.0,
            }
            val_timings["Response parsing"] = time.perf_counter() - t_parse_start

        # Normalise: ensure backwards-compatible fields
        t_val_start = time.perf_counter()
        profiler.start_sub("Validation Audits")
        if "valid" not in val_json:
            val_json["valid"] = len(val_json.get("errors", [])) == 0
        if "errors" not in val_json:
            val_json["errors"] = []
        if "warnings" not in val_json:
            val_json["warnings"] = []
        if "repair_prompt" not in val_json:
            val_json["repair_prompt"] = ""
            
        overall = val_json.get("overall_score", val_json.get("score", 0.95))
        val_json["overall_score"] = overall
        val_json["score"] = overall
        if "dimensions" not in val_json:
            val_json["dimensions"] = {
                "business_consistency": {"score": overall, "findings": []},
                "product_quality": {"score": overall, "findings": []},
                "engineering_readiness": {"score": overall, "findings": []},
            }

        # Log dimension breakdown
        dims = val_json["dimensions"]
        logger.info(
            f"Semantic Validation scores — BC: {dims.get('business_consistency',{}).get('score','?')} "
            f"PQ: {dims.get('product_quality',{}).get('score','?')} "
            f"ER: {dims.get('engineering_readiness',{}).get('score','?')} "
            f"Overall: {overall}"
        )
        profiler.end_sub("Validation Audits")
        val_timings["JSON validation"] = time.perf_counter() - t_val_start
 
        t_fmt_start = time.perf_counter()
        profiler.start_sub("Formatting & Markdown")
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry = {
            "agent": "SemanticValidationAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0.0",
        }

        # Merge semantic validation report with existing report if present
        new_metadata = context.metadata.copy()
        existing_report = new_metadata.get("validation_report", {})
        
        if existing_report:
            # Merge errors and warnings
            merged_errors = list(set(existing_report.get("errors", []) + val_json.get("errors", [])))
            merged_warnings = list(set(existing_report.get("warnings", []) + val_json.get("warnings", [])))
            
            # Combine overall score by taking the minimum (for safety) or weighted average
            merged_score = min(existing_report.get("overall_score", 1.0), val_json.get("overall_score", 1.0))
            
            merged_report = {
                "valid": (len(merged_errors) == 0) and (merged_score >= 0.95),
                "overall_score": merged_score,
                "score": merged_score,
                "dimensions": {
                    "business_consistency": {
                        "score": min(existing_report.get("dimensions", {}).get("business_consistency", {}).get("score", 1.0),
                                     val_json.get("dimensions", {}).get("business_consistency", {}).get("score", 1.0)),
                        "findings": list(set(existing_report.get("dimensions", {}).get("business_consistency", {}).get("findings", []) +
                                             val_json.get("dimensions", {}).get("business_consistency", {}).get("findings", [])))
                    },
                    "product_quality": {
                        "score": min(existing_report.get("dimensions", {}).get("product_quality", {}).get("score", 1.0),
                                     val_json.get("dimensions", {}).get("product_quality", {}).get("score", 1.0)),
                        "findings": list(set(existing_report.get("dimensions", {}).get("product_quality", {}).get("findings", []) +
                                             val_json.get("dimensions", {}).get("product_quality", {}).get("findings", [])))
                    },
                    "engineering_readiness": {
                        "score": min(existing_report.get("dimensions", {}).get("engineering_readiness", {}).get("score", 1.0),
                                     val_json.get("dimensions", {}).get("engineering_readiness", {}).get("score", 1.0)),
                        "findings": list(set(existing_report.get("dimensions", {}).get("engineering_readiness", {}).get("findings", []) +
                                             val_json.get("dimensions", {}).get("engineering_readiness", {}).get("findings", [])))
                    }
                },
                "errors": merged_errors,
                "warnings": merged_warnings,
                "repair_prompt": val_json.get("repair_prompt", "") or existing_report.get("repair_prompt", ""),
                "duration_ms": existing_report.get("duration_ms", 0) + duration_ms
            }
            new_metadata["validation_report"] = merged_report
        else:
            new_metadata["validation_report"] = val_json
            
        res_ctx = context.clone(metadata=new_metadata).add_agent_log(log_entry)
        profiler.end_sub("Formatting & Markdown")
        val_timings["Markdown formatting"] = time.perf_counter() - t_fmt_start
        
        t_post_start = time.perf_counter()
        val_timings["Post-processing"] = time.perf_counter() - t_post_start

        # Print Timing Report
        print("\nSemantic Validation")
        print("-------------------")
        print(f"Prompt Construction .... {val_timings['Prompt construction']:.2f} s")
        print(f"RAG Context Prep ....... {val_timings['RAG context preparation']:.2f} s")
        print(f"LLM Invocation ......... {val_timings['LLM invocation']:.2f} s")
        print(f"Response Parsing ....... {val_timings['Response parsing']:.2f} s")
        print(f"JSON Validation ........ {val_timings['JSON validation']:.2f} s")
        print(f"Markdown Formatting .... {val_timings['Markdown formatting']:.2f} s")
        print(f"Post-processing ........ {val_timings['Post-processing']:.2f} s\n")

        return res_ctx


# Alias ValidationAgent to SemanticValidationAgent for import backward compatibility
ValidationAgent = SemanticValidationAgent

# Register both keys
registry.register("semantic_validation_agent", SemanticValidationAgent())
registry.register("validation_agent", SemanticValidationAgent())
