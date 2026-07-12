import json
import logging
from typing import Dict, Any
from backend.llm import get_llm
from backend.prompts import WORKSPACE_EDITOR_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def update_workspace(workspace: Dict[str, Any], instruction: str) -> Dict[str, Any]:
    """Refines the existing workspace deliverables based on user instructions.
    
    Args:
        workspace (dict): The complete active workspace project dictionary.
        instruction (str): User refinement instruction.
        
    Returns:
        dict: The updated workspace project dictionary with updated deliverables content.
        
    Raises:
        ValueError: If inputs are invalid or LLM parsing fails.
        RuntimeError: If LLM execution fails.
    """
    if not workspace:
        raise ValueError("Workspace cannot be empty.")
    if not instruction.strip():
        raise ValueError("Refinement instruction cannot be empty.")
        
    logger.info(f"Applying workspace refinement instruction: '{instruction[:50]}...'")
    
    # Prepare context payload excluding verbose deliverable structures if they are unmodified
    context_payload = {
        "name": workspace.get("name", "Unknown Project"),
        "idea": workspace.get("idea", ""),
        "industry": workspace.get("industry", ""),
        "product_type": workspace.get("product_type", ""),
        "audience": workspace.get("audience", ""),
        "deliverables": workspace.get("deliverables", {})
    }
    
    user_message = f"""Workspace Details:
{json.dumps(context_payload, indent=2)}

User Refinement Instruction:
{instruction}
"""
    
    logger.info("Invoking LLM for Workspace Editor refinement...")
    llm = get_llm()
    messages = [
        ("system", WORKSPACE_EDITOR_SYSTEM_PROMPT),
        ("user", user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()
    except Exception as e:
        logger.error(f"Error invoking Groq LLM: {e}")
        raise RuntimeError(f"LLM invocation failed: {e}")
        
    # Clean markdown code fences if returned by the LLM
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()
        
    try:
        updated_deliverables = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON. Raw response:\n{raw_text}")
        raise ValueError(f"LLM returned invalid JSON: {e}. Raw response: {raw_text}") from e
        
    # Robustly handle LLM outputs that might return the full outer schema
    if "deliverables" in updated_deliverables:
        if isinstance(updated_deliverables["deliverables"], dict):
            updated_deliverables = updated_deliverables["deliverables"]
            
    # Update the deliverables inside the workspace dict
    new_workspace = dict(workspace)
    new_workspace["deliverables"] = updated_deliverables
    
    logger.info("Workspace refinement successfully completed and updated.")
    return new_workspace
