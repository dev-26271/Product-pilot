import json
import logging
from typing import Dict, Any
from rag import retrieve_product
from backend.llm import get_llm
from backend.prompts import PRODUCT_MANAGER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def generate_product_requirements(business_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Generates structured Product Requirements JSON based on RAG context and Business Analysis.
    
    Args:
        business_analysis (dict): Output from the Business Analyst agent.
        
    Returns:
        dict: Parsed and validated Product Requirements JSON.
        
    Raises:
        ValueError: If business_analysis input is empty or parsing generated JSON fails.
        RuntimeError: If LLM invocation fails.
    """
    if not business_analysis:
        raise ValueError("business_analysis input cannot be empty.")
        
    # Step 1: Extract context components from Business Analysis JSON
    problem = business_analysis.get("Problem Statement", "")
    goals = " ".join(business_analysis.get("Business Goals", []))
    personas = " ".join([
        f"{p.get('name')} {p.get('role')} {p.get('needs')}" 
        for p in business_analysis.get("User Personas", [])
    ])
    
    # Step 2: Build a retrieval query focusing on goals, personas, scope and problems
    retrieval_query = f"{problem} {goals} {personas}".strip()
    logger.info(f"Building retrieval query for Product KB: '{retrieval_query[:80]}...'")
    
    # Step 3: Retrieve top 3 relevant chunks from the Product knowledge base
    context_docs = retrieve_product(retrieval_query, k=3)
    context_str = "\n\n".join([doc.page_content for doc in context_docs])
    logger.info(f"Retrieved {len(context_docs)} chunks from product index.")
    
    # Step 4: Build prompt combining System Prompt + Context + Business Analysis JSON
    user_message = f"""Retrieved Product Context:
{context_str}

Business Analysis JSON:
{json.dumps(business_analysis, indent=2)}
"""
    
    # Step 5: Invoke the Groq Model using ChatGroq instance
    logger.info("Invoking LLM for Product Requirements generation...")
    llm = get_llm()
    messages = [
        ("system", PRODUCT_MANAGER_SYSTEM_PROMPT),
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
        
    # Step 6 & 7: Parse and validate JSON
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON. Raw response:\n{raw_text}")
        raise ValueError(f"LLM returned invalid JSON: {e}. Raw response: {raw_text}") from e
        
    # Check expected keys in JSON schema
    required_keys = ["Features", "Roadmap"]
    for key in required_keys:
        if key not in data:
            logger.warning(f"Key '{key}' is missing from generated Product Requirements JSON.")
            
    logger.info("Product Requirements successfully generated and validated.")
    return data
