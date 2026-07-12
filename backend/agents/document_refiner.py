import json
import logging
from typing import Dict, Any
from backend.llm import get_llm
from backend.prompts import DOCUMENT_REFINER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def refine_document(
    document_name: str, 
    current_content: Dict[str, Any], 
    instruction: str, 
    workspace: Dict[str, Any]
) -> Dict[str, Any]:
    """Refines a specific document using LLM based on refinement instruction."""
    logger.info(f"Refining document '{document_name}' based on instruction: '{instruction[:50]}'")
    
    user_message = f"""Workspace Metadata:
Project Name: {workspace.get('name')}
Idea: {workspace.get('idea')}
Industry: {workspace.get('industry')}
Product Type: {workspace.get('product_type')}
Audience: {workspace.get('audience')}

Document to Refine: {document_name}
Current Content:
{json.dumps(current_content, indent=2)}

Refinement Instruction:
{instruction}
"""
    llm = get_llm()
    messages = [
        ("system", DOCUMENT_REFINER_SYSTEM_PROMPT),
        ("user", user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()
    except Exception as e:
        logger.error(f"Error invoking Groq LLM in Document Refiner: {e}")
        raise RuntimeError(f"LLM invocation failed: {e}")
        
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines[-1].startswith("```"): lines = lines[:-1]
        raw_text = "\n".join(lines).strip()
        
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Document Refiner response as JSON: {e}. Response: {raw_text}")
        raise ValueError(f"Invalid JSON returned: {e}") from e
        
    logger.info(f"Document '{document_name}' refinement complete and validated.")
    return data
