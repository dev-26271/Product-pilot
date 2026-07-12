import json
import logging
from typing import Dict, Any, List
from backend.llm import get_llm
from backend.prompts import WORKSPACE_CHAT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def chat_refine_workspace(
    workspace: Dict[str, Any], 
    chat_history: List[Dict[str, str]], 
    user_message: str
) -> Dict[str, Any]:
    """Runs the senior PM chat workflow to refine deliverables or answer questions.
    
    Args:
        workspace (dict): Complete active project workspace dictionary.
        chat_history (list): List of dicts representing conversation history.
        user_message (str): The new instruction or question from the user.
        
    Returns:
        dict: Parsed LLM response containing 'chat_response', 'updated_tabs', and 'deliverables'.
    """
    logger.info(f"Triggering PM refinement chat. User message: '{user_message[:50]}...'")
    
    # Prepare context payload excluding verbose deliverable structures if they are unmodified
    context_payload = {
        "name": workspace.get("name", "Unknown Project"),
        "idea": workspace.get("idea", ""),
        "industry": workspace.get("industry", ""),
        "product_type": workspace.get("product_type", ""),
        "audience": workspace.get("audience", ""),
        "deliverables": workspace.get("deliverables", {})
    }
    
    # Format chat history context for the LLM
    history_str = ""
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Senior PM"
        history_str += f"{role}: {msg['content']}\n"
        
    user_prompt = f"""Workspace Details:
{json.dumps(context_payload, indent=2)}

Conversation History:
{history_str}

New User Message:
User: {user_message}
"""

    logger.info("Invoking LLM for PM chat agent...")
    llm = get_llm()
    messages = [
        ("system", WORKSPACE_CHAT_SYSTEM_PROMPT),
        ("user", user_prompt)
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
        result_data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON. Raw response:\n{raw_text}")
        raise ValueError(f"LLM returned invalid JSON: {e}. Raw response: {raw_text}") from e
        
    # Validate expected keys
    required_keys = ["chat_response", "updated_tabs", "deliverables"]
    for key in required_keys:
        if key not in result_data:
            logger.warning(f"Key '{key}' is missing from PM chat response JSON.")
            
    # Robustly handle nested deliverables structures if returned double-nested
    if "deliverables" in result_data:
        deliv = result_data["deliverables"]
        if "deliverables" in deliv:
            result_data["deliverables"] = deliv["deliverables"]
            
    logger.info("PM chat response successfully generated and validated.")
    return result_data
