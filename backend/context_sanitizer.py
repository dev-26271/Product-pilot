import json
from typing import Dict, Any

def compress_business_analysis(ba: Dict[str, Any]) -> str:
    """Compresses Business Analysis JSON to remove metadata and flatten structure."""
    if not ba:
        return ""
    
    lines = []
    
    # 1. Problem Statement
    ps = ba.get("problem_statement", {})
    if isinstance(ps, dict):
        ps_text = ps.get("text", "")
        ps_id = ps.get("id", "PS-001")
    else:
        ps_text = str(ps)
        ps_id = "PS-001"
    if ps_text:
        lines.append(f"Problem Statement [{ps_id}]: {ps_text}")
    
    # 2. Business Goals
    goals = ba.get("business_goals", [])
    if goals:
        lines.append("\nBusiness Goals:")
        for g in goals:
            if not isinstance(g, dict):
                continue
            gid = g.get("id", "BG-???")
            goal_text = g.get("goal", "")
            lines.append(f"- Goal {gid}: {goal_text}")
            kpi = g.get("kpi")
            target = g.get("target_value")
            timeline = g.get("timeline")
            if kpi or target or timeline:
                lines.append(f"  KPI: {kpi} | Target: {target} | Timeline: {timeline}")
                
    # 3. User Personas
    personas = ba.get("user_personas", [])
    if personas:
        lines.append("\nUser Personas:")
        for p in personas:
            if not isinstance(p, dict):
                continue
            pid = p.get("id", "PE-???")
            name = p.get("name", "")
            role = p.get("role", "")
            lines.append(f"- Persona {pid}: {name} ({role})")
            
            # Goals / Needs
            goals_list = p.get("goals") or p.get("needs") or []
            if isinstance(goals_list, list):
                goals_str = ", ".join(goals_list)
            else:
                goals_str = str(goals_list)
            if goals_str:
                lines.append(f"  Primary Goals: {goals_str}")
                
            # Frustrations / Pain Points
            frust = p.get("frustrations") or p.get("pain_points") or []
            if isinstance(frust, list):
                frust_str = ", ".join(frust)
            else:
                frust_str = str(frust)
            if frust_str:
                lines.append(f"  Pain Points: {frust_str}")
                
            # Workflow
            wf = p.get("workflow") or p.get("daily_workflow")
            if wf:
                lines.append(f"  Workflow: {wf}")
                
    return "\n".join(lines)


def compress_intent_context(intent: Dict[str, Any]) -> str:
    """Compresses Intent Context JSON to flatten list structures and simplify tags."""
    if not intent:
        return ""
    
    lines = []
    
    project_name = intent.get("project_name")
    if project_name:
        lines.append(f"Project Name: {project_name}")
        
    industry = intent.get("industry")
    if isinstance(industry, dict):
        ind_val = industry.get("value")
    else:
        ind_val = industry
    if ind_val:
        lines.append(f"Industry: {ind_val}")
        
    product_type = intent.get("product_type")
    if isinstance(product_type, dict):
        pt_val = product_type.get("value")
    else:
        pt_val = product_type
    if pt_val:
        lines.append(f"Product Type: {pt_val}")
        
    audience = intent.get("audience")
    if isinstance(audience, dict):
        aud_val = audience.get("value")
    else:
        aud_val = audience
    if aud_val:
        lines.append(f"Audience: {aud_val}")
        
    prob = intent.get("problem_statement")
    if prob:
        lines.append(f"Problem Statement: {prob}")
        
    features = intent.get("core_features") or []
    if features:
        lines.append("Core Features:")
        for f in features:
            lines.append(f"- {f}")
            
    return "\n".join(lines)


def compress_metadata(meta: Dict[str, Any]) -> str:
    """Compresses Metadata dictionary to keep only essential configuration attributes."""
    if not meta:
        return "{}"
    
    keys_of_interest = ["industry", "product_type", "audience", "risk_analysis"]
    cleaned = {}
    for k in keys_of_interest:
        if k in meta:
            cleaned[k] = meta[k]
            
    return json.dumps(cleaned, indent=2)
