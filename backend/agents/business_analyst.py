import json
import logging
from typing import Dict, Any
from rag import retrieve_business
from backend.llm import get_llm
from backend.prompts import BUSINESS_ANALYST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def generate_business_analysis(user_input: Dict[str, Any]) -> Dict[str, Any]:
    """Generates structured Business Analysis JSON based on RAG context and user inputs.
    
    Args:
        user_input (dict): Dict containing 'idea', 'industry', etc.
        
    Returns:
        dict: Parsed and validated Business Analysis JSON.
        
    Raises:
        ValueError: If user_input idea is empty or parsing generated JSON fails.
        RuntimeError: If LLM invocation fails.
    """
    idea = user_input.get("idea", "")
    if not idea:
        raise ValueError("Product idea cannot be empty inside user_input.")
        
    logger.info(f"Retrieving context for idea: '{idea[:50]}...'")
    
    # Step 1: Call retrieve_business using product idea
    # Step 2: Retrieve top 3 relevant chunks
    context_docs = retrieve_business(idea, k=3)
    context_str = "\n\n".join([doc.page_content for doc in context_docs])
    logger.info(f"Retrieved {len(context_docs)} chunks from business index.")
    
    # Step 3: Build final prompt
    user_message = f"""Context:
{context_str}

User Input:
Product Idea: {idea}
Industry: {user_input.get("industry", "Unknown")}
Product Type: {user_input.get("product_type", "Unknown")}
Audience: {user_input.get("audience", "Unknown")}
"""
    
    # Step 4: Invoke the Groq Model
    logger.info("Invoking LLM for Business Analysis generation...")
    llm = get_llm()
    messages = [
        ("system", BUSINESS_ANALYST_SYSTEM_PROMPT),
        ("user", user_message)
    ]
    
    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()
    except Exception as e:
        logger.error(f"Error invoking Groq LLM: {e}")
        raise RuntimeError(f"LLM invocation failed: {e}")
        
    # Clean any markdown code fences if returned by the LLM
    if raw_text.startswith("```"):
        lines = raw_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        raw_text = "\n".join(lines).strip()
        
    # Step 5 & 6: Parse and validate JSON response
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON. Raw response:\n{raw_text}")
        raise ValueError(f"LLM returned invalid JSON: {e}. Raw response: {raw_text}") from e
        
    # Check expected keys in JSON schema
    required_keys = ["Problem Statement", "Business Goals", "User Personas"]
    for key in required_keys:
        if key not in data:
            logger.warning(f"Key '{key}' is missing from generated Business Analysis JSON.")
            
    logger.info("Business Analysis successfully generated and validated.")
    return data
