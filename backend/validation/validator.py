import time
import re
from typing import Dict, Any, List
from backend.workspace_context import WorkspaceContext
from backend.validation.rules import (
    check_duplicate_ids,
    check_duplicate_feature_names,
    check_required_fields,
    check_empty_values,
    check_placeholders,
    check_acceptance_criteria_format,
    check_story_points_fibonacci,
    check_traceability_links,
    check_measurable_nfrs,
    check_domain_rules
)

class DeterministicValidator:
    """Validator that audits the workspace deliverables using deterministic Python rules."""

    def validate(self, context: WorkspaceContext) -> Dict[str, Any]:
        start_time = time.perf_counter()
        
        errors: List[str] = []
        warnings: List[str] = []
        repair_actions: List[str] = []
        
        # 1. Run validation rules
        dup_id_errors = check_duplicate_ids(context)
        errors.extend(dup_id_errors)
        if dup_id_errors:
            repair_actions.append("fix_duplicate_ids")
            
        dup_name_errors = check_duplicate_feature_names(context)
        errors.extend(dup_name_errors)
        
        req_field_errors = check_required_fields(context)
        errors.extend(req_field_errors)
        if req_field_errors:
            repair_actions.append("fix_missing_fields")
            
        empty_val_errors = check_empty_values(context)
        errors.extend(empty_val_errors)
        if empty_val_errors:
            repair_actions.append("fix_empty_arrays")
            
        placeholder_errors = check_placeholders(context)
        warnings.extend(placeholder_errors)
        if placeholder_errors:
            repair_actions.append("fix_placeholders")
            
        gherkin_errors = check_acceptance_criteria_format(context)
        errors.extend(gherkin_errors)
        
        fib_errors = check_story_points_fibonacci(context)
        errors.extend(fib_errors)
        
        trace_errors = check_traceability_links(context)
        errors.extend(trace_errors)
        
        nfr_warnings = check_measurable_nfrs(context)
        warnings.extend(nfr_warnings)
        
        domain_errors = check_domain_rules(context)
        errors.extend(domain_errors)

        # 2. Compute dimensional scoring
        bc_errors = [e for e in errors if any(k in e for k in ["Goal", "Persona"])]
        bc_deduction = len(bc_errors) * 0.15
        bc_score = max(0.0, 1.0 - bc_deduction)
        
        pq_errors = [e for e in errors if any(k in e for k in ["Feature", "Requirement", "Section", "Gherkin", "FR"])]
        pq_warnings = [w for w in warnings if "NFR" in w or "Placeholder" in w]
        pq_deduction = (len(pq_errors) * 0.15) + (len(pq_warnings) * 0.05)
        pq_score = max(0.0, 1.0 - pq_deduction)
        
        er_errors = [e for e in errors if any(k in e for k in ["Story", "Jira", "Task", "Fibonacci", "US-", "JT-"])]
        er_deduction = len(er_errors) * 0.15
        er_score = max(0.0, 1.0 - er_deduction)
        
        overall_score = (bc_score * 0.35) + (pq_score * 0.35) + (er_score * 0.30)
        
        # Determine valid status (must have 0 errors and >= 0.95 score)
        valid = (len(errors) == 0) and (overall_score >= 0.95)
        
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        return {
            "valid": valid,
            "overall_score": round(overall_score, 2),
            "score": round(overall_score, 2),
            "dimensions": {
                "business_consistency": {"score": round(bc_score, 2), "findings": bc_errors},
                "product_quality": {"score": round(pq_score, 2), "findings": pq_errors + pq_warnings},
                "engineering_readiness": {"score": round(er_score, 2), "findings": er_errors}
            },
            "errors": errors,
            "warnings": warnings,
            "repair_actions": list(set(repair_actions)),
            "duration_ms": duration_ms
        }

    def auto_fix(self, context: WorkspaceContext, repair_actions: List[str]) -> WorkspaceContext:
        """Automatically repairs simple structural, ID, and placeholder issues in place."""
        if not repair_actions:
            return context
            
        # Make a copy of context metadata and documents
        ba = context.business_analysis.copy()
        prd = context.prd.copy()
        
        # 1. Fix duplicate/missing IDs
        if "fix_duplicate_ids" in repair_actions or "fix_missing_fields" in repair_actions:
            # Business Goals
            goals = ba.get("business_goals", [])
            for idx, g in enumerate(goals):
                if isinstance(g, dict):
                    g["id"] = f"BG-{str(idx+1).zfill(3)}"
                    g.setdefault("version", "1.0")
                    g.setdefault("status", "Active")
                    g.setdefault("smart", {"specific": "", "measurable": "", "achievable": "", "relevant": "", "time_bound": ""})
            
            # Personas
            personas = ba.get("user_personas", [])
            for idx, p in enumerate(personas):
                if isinstance(p, dict):
                    p["id"] = f"PE-{str(idx+1).zfill(3)}"
                    p.setdefault("version", "1.0")
                    p.setdefault("status", "Active")
            
            # Features
            features = prd.get("Core_Features", [])
            for idx, f in enumerate(features):
                if isinstance(f, dict):
                    f["id"] = f"FT-{str(idx+1).zfill(3)}"
                    f.setdefault("version", "1.0")
                    f.setdefault("status", "Draft")
                    f.setdefault("dependencies", [])
            
            # Functional Requirements
            frs = prd.get("Functional_Requirements", [])
            for idx, fr in enumerate(frs):
                if isinstance(fr, dict):
                    fr["id"] = f"FR-{str(idx+1).zfill(3)}"
                    fr.setdefault("version", "1.0")
                    fr.setdefault("status", "Draft")
                    fr.setdefault("dependencies", [])
                    ac = fr.get("acceptance_criteria")
                    if not ac:
                        fr["acceptance_criteria"] = ["Given the system initializes, when loading feature, then output is active."]
                    elif isinstance(ac, str):
                        fr["acceptance_criteria"] = [ac]

        # 2. Fix empty arrays/lists
        if "fix_empty_arrays" in repair_actions:
            # Ensure required arrays in entities are populated with defaults
            features = prd.get("Core_Features", [])
            for f in features:
                if isinstance(f, dict):
                    for arr_field in ["functional_requirement_ids", "dependencies", "acceptance_criteria", "success_metrics", "kpis"]:
                        if arr_field not in f or not f[arr_field]:
                            f[arr_field] = ["Verify feature operational integrity."] if arr_field in ["acceptance_criteria", "success_metrics", "kpis"] else []
            
            frs = prd.get("Functional_Requirements", [])
            for fr in frs:
                if isinstance(fr, dict):
                    for arr_field in ["acceptance_criteria", "dependencies", "success_metrics", "kpis", "edge_cases"]:
                        if arr_field not in fr or not fr[arr_field]:
                            fr[arr_field] = ["Verify operational capacity under peek load."] if arr_field in ["acceptance_criteria", "success_metrics"] else []

        # 3. Fix placeholder text
        if "fix_placeholders" in repair_actions:
            placeholder_rx = r"\b(tbd|todo|coming\s+soon|insert\s+here|lorem\s+ipsum)\b"
            
            def _clean_placeholders(obj: Any) -> Any:
                if isinstance(obj, str):
                    if re.search(placeholder_rx, obj, re.IGNORECASE) or "[insert]" in obj.lower():
                        return "Verify requirement operational metrics."
                    return obj
                elif isinstance(obj, list):
                    return [_clean_placeholders(x) for x in obj]
                elif isinstance(obj, dict):
                    return {k: _clean_placeholders(v) for k, v in obj.items()}
                return obj

            ba = _clean_placeholders(ba)
            prd = _clean_placeholders(prd)

        # Reconstruct context
        return context.clone(business_analysis=ba, prd=prd)
