import json
import logging
from typing import Dict, Any
from backend.llm import get_llm
from backend.prompts import ROADMAP_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def generate_roadmap(workspace: Dict[str, Any]) -> Dict[str, Any]:
    """Generates Product Roadmap JSON using LLM.
    
    Context: Original idea and existing PRD.
    """
    logger.info(f"Roadmap Agent generating roadmap for project '{workspace.get('name')}'...")
    
    prd = workspace.get('deliverables', {}).get('Product Requirements Document (PRD)', {})
    
    # User Stories may be stored as structured JSON {"epics":[...], "stories":[...]}
    # Pull epics for release/phase alignment in roadmap generation.
    raw_us = workspace.get('deliverables', {}).get('User Stories', {})
    if isinstance(raw_us, dict) and 'epics' in raw_us:
        us_epics_context = raw_us.get('epics', [])
    else:
        us_epics_context = []
    
    user_message = f"""Project Context:
Idea: {workspace.get('idea')}
Industry: {workspace.get('industry')}
Product Type: {workspace.get('product_type')}
Audience: {workspace.get('audience')}

Existing PRD:
{json.dumps(prd, indent=2)}

User Story Epics (use release fields to align roadmap phases):
{json.dumps(us_epics_context, indent=2) if us_epics_context else "Not generated yet. Build roadmap from the PRD only."}
"""

    llm = get_llm()
    messages = [
        ("system", ROADMAP_AGENT_SYSTEM_PROMPT),
        ("user", user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()
    except Exception as e:
        logger.error(f"Error invoking Groq LLM in Roadmap Agent: {e}")
        raise RuntimeError(f"LLM invocation failed: {e}")
        
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines[-1].startswith("```"): lines = lines[:-1]
        raw_text = "\n".join(lines).strip()
        
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Roadmap agent response as JSON: {e}. Response: {raw_text}")
        raise ValueError(f"Invalid JSON returned: {e}") from e
        
    logger.info("Roadmap generation complete and validated.")
    return data
