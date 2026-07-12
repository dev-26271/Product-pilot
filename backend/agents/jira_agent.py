import json
import logging
from typing import Dict, Any
from backend.llm import get_llm
from backend.prompts import JIRA_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def generate_jira_tasks(workspace: Dict[str, Any]) -> Dict[str, Any]:
    """Generates Jira Tasks JSON using LLM."""
    logger.info(f"Jira Agent generating tasks for project '{workspace.get('name')}'...")
    
    user_message = f"""Project Context:
Idea: {workspace.get('idea')}
Industry: {workspace.get('industry')}
Product Type: {workspace.get('product_type')}
Audience: {workspace.get('audience')}
Existing PRD: {json.dumps(workspace.get('deliverables', {}).get('Product Requirements Document (PRD)', {}), indent=2)}
"""
    llm = get_llm()
    messages = [
        ("system", JIRA_AGENT_SYSTEM_PROMPT),
        ("user", user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()
    except Exception as e:
        logger.error(f"Error invoking Groq LLM in Jira Agent: {e}")
        raise RuntimeError(f"LLM invocation failed: {e}")
        
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines[-1].startswith("```"): lines = lines[:-1]
        raw_text = "\n".join(lines).strip()
        
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Jira agent response as JSON: {e}. Response: {raw_text}")
        raise ValueError(f"Invalid JSON returned: {e}") from e
        
    logger.info("Jira Tasks generation complete and validated.")
    return data
