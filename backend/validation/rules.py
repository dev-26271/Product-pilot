import re
from typing import List, Dict, Any
from backend.workspace_context import WorkspaceContext

PLACEHOLDER_PATTERNS = [
    r"\btbd\b",
    r"\btodo\b",
    r"\bcoming\s+soon\b",
    r"\binsert\s+here\b",
    r"\blorem\s+ipsum\b",
    r"\[insert\]"
]

MEASURABLE_NFR_PATTERNS = [
    r"\b\d+(\.\d+)?\s*(ms|s|%|kb|mb|gb|tb|req/sec|tps|users)\b",
    r"\b99\.\d+\b",  # Uptime percentages
    r"\b\d+,\d+\b",  # Numeric constraints like 10,000
    r"\b\d+\b",     # Generic numbers
]

def check_duplicate_ids(context: WorkspaceContext) -> List[str]:
    errors = []
    
    # 1. Business Goals IDs
    goals = context.business_analysis.get("business_goals", [])
    goal_ids = []
    for g in goals:
        if isinstance(g, dict) and "id" in g:
            goal_ids.append(g["id"])
    if len(goal_ids) != len(set(goal_ids)):
        errors.append("Duplicate Business Goal IDs detected in Business Analysis.")
        
    # 2. Persona IDs
    personas = context.business_analysis.get("user_personas", [])
    persona_ids = []
    for p in personas:
        if isinstance(p, dict) and "id" in p:
            persona_ids.append(p["id"])
    if len(persona_ids) != len(set(persona_ids)):
        errors.append("Duplicate Persona IDs detected in Business Analysis.")
        
    # 3. Features IDs
    features = context.prd.get("Core_Features", [])
    feat_ids = []
    for f in features:
        if isinstance(f, dict) and "id" in f:
            feat_ids.append(f["id"])
    if len(feat_ids) != len(set(feat_ids)):
        errors.append("Duplicate Feature IDs detected in PRD.")
        
    # 4. Functional Requirement IDs
    frs = context.prd.get("Functional_Requirements", [])
    fr_ids = []
    for fr in frs:
        if isinstance(fr, dict) and "id" in fr:
            fr_ids.append(fr["id"])
    if len(fr_ids) != len(set(fr_ids)):
        errors.append("Duplicate Functional Requirement IDs detected in PRD.")
        
    # 5. User Stories IDs
    us_data = context.deliverables.get("User Stories", {})
    stories = us_data.get("entities", {}).get("stories", []) or us_data.get("content", {}).get("stories", []) or []
    us_ids = []
    for story in stories:
        if isinstance(story, dict) and "id" in story:
            us_ids.append(story["id"])
    if len(us_ids) != len(set(us_ids)):
        errors.append("Duplicate User Story IDs detected in User Stories.")
        
    # 6. Jira Tasks IDs
    jt_data = context.deliverables.get("Jira Tasks", {})
    tasks = jt_data.get("entities", {}).get("tasks", []) or jt_data.get("content", {}).get("tasks", []) or []
    jt_ids = []
    for t in tasks:
        if isinstance(t, dict) and "id" in t:
            jt_ids.append(t["id"])
    if len(jt_ids) != len(set(jt_ids)):
        errors.append("Duplicate Jira Task IDs detected in Jira Tasks.")
        
    return errors

def check_duplicate_feature_names(context: WorkspaceContext) -> List[str]:
    errors = []
    features = context.prd.get("Core_Features", [])
    names = []
    for f in features:
        if isinstance(f, dict) and "name" in f:
            names.append(f["name"].strip().lower())
    if len(names) != len(set(names)):
        errors.append("Duplicate Feature Names detected in PRD Core Features.")
    return errors

def check_required_fields(context: WorkspaceContext) -> List[str]:
    errors = []
    
    # 1. Business Goals
    goals = context.business_analysis.get("business_goals", [])
    for g in goals:
        if isinstance(g, dict):
            gid = g.get("id", "BG-???")
            for req in ["id", "goal", "smart", "owner", "kpi", "target_value"]:
                if req not in g or not g[req]:
                    errors.append(f"Business Goal {gid} is missing required field: '{req}'")
                    
    # 2. User Personas
    personas = context.business_analysis.get("user_personas", [])
    for p in personas:
        if isinstance(p, dict):
            pid = p.get("id", "PE-???")
            for req in ["id", "name", "role", "goals", "pain_points" if "pain_points" in p else "frustrations", "daily_workflow" if "daily_workflow" in p else "workflow"]:
                if req not in p or not p[req]:
                    errors.append(f"User Persona {pid} is missing required field: '{req}'")
                    
    # 3. Core Features
    features = context.prd.get("Core_Features", [])
    for f in features:
        if isinstance(f, dict):
            fid = f.get("id", "FT-???")
            for req in ["id", "name", "description", "business_value", "user_persona_mapping" if "user_persona_mapping" in f else "user_persona"]:
                if req not in f or not f[req]:
                    errors.append(f"Feature {fid} is missing required field: '{req}'")
                    
    # 4. Functional Requirements
    frs = context.prd.get("Functional_Requirements", [])
    for fr in frs:
        if isinstance(fr, dict):
            frid = fr.get("id", "FR-???")
            for req in ["id", "title" if "title" in fr else "name", "description", "priority", "acceptance_criteria"]:
                if req not in fr or not fr[req]:
                    errors.append(f"Functional Requirement {frid} is missing required field: '{req}'")
                    
    # 5. User Stories
    us_data = context.deliverables.get("User Stories", {})
    stories = us_data.get("entities", {}).get("stories", []) or us_data.get("content", {}).get("stories", []) or []
    for story in stories:
        if isinstance(story, dict):
            sid = story.get("id", "US-???")
            for req in ["id", "story_statement" if "story_statement" in story else "as_a", "acceptance_criteria" if "acceptance_criteria" in story else "definition_of_done"]:
                # Accept either canonical or legacy format
                has_val = False
                if req == "story_statement" if "story_statement" in story else "as_a":
                    has_val = ("story_statement" in story and story["story_statement"]) or ("as_a" in story and story["as_a"])
                else:
                    has_val = ("acceptance_criteria" in story and story["acceptance_criteria"]) or ("definition_of_done" in story and story["definition_of_done"])
                if not has_val:
                    errors.append(f"User Story {sid} is missing required field: '{req}'")
                    
    # 6. Jira Tasks
    jt_data = context.deliverables.get("Jira Tasks", {})
    tasks = jt_data.get("entities", {}).get("tasks", []) or jt_data.get("content", {}).get("tasks", []) or []
    for t in tasks:
        if isinstance(t, dict):
            tid = t.get("id", "JT-???")
            for req in ["id", "title" if "title" in t else "summary", "estimate", "priority"]:
                if req not in t or not t[req]:
                    errors.append(f"Jira Task {tid} is missing required field: '{req}'")
                    
    return errors

def check_empty_values(context: WorkspaceContext) -> List[str]:
    errors = []
    
    # Check top-level sections in PRD
    for section_name, val in context.prd.items():
        if val is None or val == "" or (isinstance(val, (list, dict)) and len(val) == 0):
            errors.append(f"PRD Section '{section_name}' is empty.")
            
    return errors

def check_placeholders(context: WorkspaceContext) -> List[str]:
    errors = []
    
    def _scan_obj(obj: Any, path: str):
        if isinstance(obj, str):
            for pat in PLACEHOLDER_PATTERNS:
                if re.search(pat, obj, re.IGNORECASE):
                    errors.append(f"Placeholder '{obj}' detected in path: {path}")
                    break
        elif isinstance(obj, list):
            for i, val in enumerate(obj):
                _scan_obj(val, f"{path}[{i}]")
        elif isinstance(obj, dict):
            for k, val in obj.items():
                _scan_obj(val, f"{path}.{k}")

    _scan_obj(context.business_analysis, "business_analysis")
    _scan_obj(context.prd, "prd")
    
    return errors

def check_acceptance_criteria_format(context: WorkspaceContext) -> List[str]:
    errors = []
    
    frs = context.prd.get("Functional_Requirements", [])
    for fr in frs:
        if isinstance(fr, dict):
            frid = fr.get("id", "FR-???")
            ac = fr.get("acceptance_criteria", [])
            if isinstance(ac, str):
                ac = [ac]
            if not isinstance(ac, list):
                errors.append(f"Functional Requirement {frid} acceptance_criteria is not a list/string.")
                continue
                
            for idx, item in enumerate(ac):
                if not isinstance(item, str):
                    continue
                # Gherkin check: must contain Given, When, Then (not necessarily starting, but present)
                item_lower = item.lower()
                has_given = "given" in item_lower
                has_when = "when" in item_lower
                has_then = "then" in item_lower
                if not (has_given or has_when or has_then):
                    errors.append(f"FR {frid} AC[{idx}] does not follow Gherkin style (Given/When/Then): '{item}'")
                    
    return errors

def check_story_points_fibonacci(context: WorkspaceContext) -> List[str]:
    errors = []
    
    jt_data = context.deliverables.get("Jira Tasks", {})
    tasks = jt_data.get("entities", {}).get("tasks", []) or jt_data.get("content", {}).get("tasks", []) or []
    fibonacci_set = {1, 2, 3, 5, 8, 13}
    
    for t in tasks:
        if isinstance(t, dict):
            tid = t.get("id", "JT-???")
            est = t.get("estimate")
            if isinstance(est, dict):
                sp = est.get("story_points")
            else:
                sp = est
            if sp is not None:
                try:
                    sp_val = int(sp)
                    if sp_val not in fibonacci_set:
                        errors.append(f"Jira Task {tid} estimate '{sp}' is not a valid Fibonacci number (1, 2, 3, 5, 8, 13).")
                except ValueError:
                    errors.append(f"Jira Task {tid} estimate '{sp}' is not numeric.")
                    
    return errors

def check_traceability_links(context: WorkspaceContext) -> List[str]:
    errors = []
    
    # Get active entity mappings
    goals = {g["id"]: g for g in context.business_analysis.get("business_goals", []) if isinstance(g, dict) and "id" in g}
    features = {f["id"]: f for f in context.prd.get("Core_Features", []) if isinstance(f, dict) and "id" in f}
    frs = {fr["id"]: fr for fr in context.prd.get("Functional_Requirements", []) if isinstance(fr, dict) and "id" in fr}
    
    # 1. Feature -> Business Goal
    for fid, feat in features.items():
        g_map = feat.get("business_goal_mapping") or feat.get("business_goal")
        if g_map and g_map not in goals:
            errors.append(f"Feature {fid} references broken Business Goal mapping: '{g_map}'")
            
    # 2. Functional Requirement -> Feature
    for frid, fr in frs.items():
        f_map = fr.get("related_feature") or fr.get("traceability", {}).get("implements", [])
        if isinstance(f_map, str):
            f_map = [f_map]
        for fm in f_map:
            if fm and fm not in features:
                errors.append(f"Functional Requirement {frid} references broken Feature mapping: '{fm}'")
                
    # 3. User Story -> Functional Requirement
    us_data = context.deliverables.get("User Stories", {})
    stories = us_data.get("entities", {}).get("stories", []) or us_data.get("content", {}).get("stories", []) or []
    story_ids = {}
    for story in stories:
        if not isinstance(story, dict):
            continue
        sid = story.get("id", "US-???")
        story_ids[sid] = story
        fr_links = story.get("traceability", {}).get("functional_requirements", [])
        if isinstance(fr_links, str):
            fr_links = [fr_links]
        for fl in fr_links:
            if fl and fl not in frs:
                errors.append(f"User Story {sid} references broken Functional Requirement: '{fl}'")
                
    # 4. Jira Task -> User Story
    jt_data = context.deliverables.get("Jira Tasks", {})
    tasks = jt_data.get("entities", {}).get("tasks", []) or jt_data.get("content", {}).get("tasks", []) or []
    for t in tasks:
        if isinstance(t, dict):
            tid = t.get("id", "JT-???")
            us_ref = t.get("user_story_id")
            if us_ref and us_ref not in story_ids:
                errors.append(f"Jira Task {tid} references broken User Story: '{us_ref}'")
                
    return errors

def check_measurable_nfrs(context: WorkspaceContext) -> List[str]:
    warnings = []
    
    nfrs = context.prd.get("Non_Functional_Requirements", {})
    if isinstance(nfrs, str):
        # Scan raw string
        matched = False
        for pat in MEASURABLE_NFR_PATTERNS:
            if re.search(pat, nfrs, re.IGNORECASE):
                matched = True
                break
        if not matched:
            warnings.append("Non-Functional Requirements do not appear to contain measurable numeric metrics.")
    elif isinstance(nfrs, dict):
        for k, v in nfrs.items():
            if not isinstance(v, str):
                continue
            matched = False
            for pat in MEASURABLE_NFR_PATTERNS:
                if re.search(pat, v, re.IGNORECASE):
                    matched = True
                    break
            if not matched:
                warnings.append(f"Non-Functional Requirement '{k}' ('{v}') does not contain measurable numeric metrics.")
                
    return warnings

def check_domain_rules(context: WorkspaceContext) -> List[str]:
    """Validates domain-specific constraints in the PRD and Business Analysis."""
    errors = []
    
    from backend.domains import detect_domain
    domain = detect_domain(context.idea, context.intent_context)
    
    # Extract text content from the whole PRD for keyword checks
    prd_str = str(context.prd).lower()
    
    if domain == "Physical Consumer Product":
        # A towel should never require TLS encryption or DB/API.
        software_keywords = ["tls", "ssl", "encryption", "database", "api", "oauth", "jwt", "https", "concurrent users"]
        for kw in software_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', prd_str):
                errors.append(f"Physical Product contains software-specific requirement: '{kw}'.")
                
    elif domain in ["SaaS Platform", "Mobile Application", "Website", "Enterprise Software"]:
        # A SaaS should never require manufacturing tolerances.
        physical_keywords = ["manufacturing tolerances", "manufacturing requirements", "wash cycles", "packaging integrity", "shelf life", "drop-test"]
        for kw in physical_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', prd_str):
                errors.append(f"Software product contains physical product requirement: '{kw}'.")
                
    return errors
