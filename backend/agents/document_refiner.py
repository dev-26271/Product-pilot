import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import DOCUMENT_REFINER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

SECTION_REFINER_SYSTEM_PROMPT = """You are an expert Technical Product Manager.
Your task is to refine a specific section of a product document based on the user's instruction.
Return ONLY the updated text content for this section. No markdown JSON wrapping, no conversational prefix or suffix, no code fences. Output the refined content directly.
"""

class DocumentRefinerAgent(BaseAgent):
    """Document Refiner Agent that applies refinement instructions incrementally to affected sections."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing DocumentRefinerAgent (Incremental Section Refiner)...")
        start_time = time.perf_counter()
        
        document_name = kwargs.get("document_name", "")
        current_content = kwargs.get("current_content", {})
        instruction = kwargs.get("instruction", "")
        
        # 1. Resolve which sections are affected
        from backend.agents.dependency_analyzer import DependencyAnalyzer
        analyzer = DependencyAnalyzer()
        
        affected_sections = []
        if document_name == "Product Requirements Document (PRD)":
            affected_sections = analyzer.analyze_prd_sections(instruction)
        else:
            # For Business Analysis or other documents, refine everything if it's not split into dict
            if isinstance(current_content, dict):
                affected_sections = list(current_content.keys())
            else:
                affected_sections = [document_name]

        logger.info(f"Target sections for incremental refinement: {affected_sections}")
        
        # 2. Iterate and refine each affected section incrementally
        updated_content = current_content.copy() if isinstance(current_content, dict) else current_content
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        total_tokens = 0
        
        CANONICAL_SCHEMA_KEYS = {
            "📋 Executive Summary": "Executive_Summary",
            "🔭 Product Vision": "Product_Vision",
            "🎯 Problem Statement": "Problem_Statement",
            "👥 User Personas": "User_Personas",
            "📈 Goals & Objectives": "Goals_and_Objectives",
            "⚙️ Functional Requirements": "Functional_Requirements",
            "🔒 Non-Functional Requirements": "Non_Functional_Requirements",
            "✨ Core Features": "Core_Features",
            "💡 Assumptions": "Assumptions",
            "🚧 Constraints": "Constraints",
            "📊 Success Metrics": "Success_Metrics",
            "📅 High-Level Roadmap": "High_Level_Roadmap",
            "❓ Open Questions": "Open_Questions"
        }

        if isinstance(current_content, dict):
            # Check if dict contains structured schema keys
            is_schema_dict = "Functional_Requirements" in current_content or "Core_Features" in current_content or "User_Personas" in current_content
            
            for section in affected_sections:
                key_to_use = section
                if is_schema_dict:
                    key_to_use = CANONICAL_SCHEMA_KEYS.get(section, section)
                    
                if key_to_use not in current_content:
                    # Fallback matching (e.g. "Functional Requirements" or "Core Features")
                    fallback_key = section.split(" ", 1)[-1] if " " in section else section
                    if fallback_key in current_content:
                        key_to_use = fallback_key
                    elif "Functional_Requirements" in current_content and "Functional" in section:
                        key_to_use = "Functional_Requirements"
                    elif "Core_Features" in current_content and "Feature" in section:
                        key_to_use = "Core_Features"
                    else:
                        continue
                    
                section_text = current_content[key_to_use]
                logger.info(f"Refining section: '{key_to_use}'")
                
                user_message = f"""Document: {document_name}
Section: {key_to_use}
Current Content:
{json.dumps(section_text, indent=2) if isinstance(section_text, (dict, list)) else str(section_text)}

Refinement Instruction:
{instruction}
"""
                messages = [
                    ("system", SECTION_REFINER_SYSTEM_PROMPT),
                    ("user", user_message)
                ]
                
                try:
                    response = llm.invoke(messages)
                    refined_text = response.content.strip()
                    # Clean fences if LLM wrapped it anyway
                    if refined_text.startswith("```"):
                        lines = refined_text.splitlines()
                        refined_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:]).strip()
                    
                    # If the original section was structured list of dicts, try parsing refined_text back as JSON
                    if isinstance(section_text, list):
                        try:
                            # If it didn't return JSON, try wrapping it in JSON block instructions or fallback to text
                            if "```json" in refined_text:
                                refined_text = refined_text.split("```json")[1].split("```")[0].strip()
                            elif refined_text.startswith("```"):
                                refined_text = refined_text.splitlines()[1:-1]
                            parsed_list = json.loads(refined_text)
                            if isinstance(parsed_list, list):
                                updated_content[key_to_use] = parsed_list
                            else:
                                updated_content[key_to_use] = [{"description": refined_text}]
                        except Exception:
                            # Parse failed: save as text under description list
                            updated_content[key_to_use] = [{"description": refined_text}]
                    else:
                        updated_content[key_to_use] = refined_text
                    
                    total_tokens += len(refined_text) // 4
                except Exception as sect_err:
                    logger.error(f"Failed to refine section '{key_to_use}': {sect_err}")
        else:
            # Fallback to full document refinement if content is flat string
            user_message = f"""=== INTENT CONTEXT ===
{json.dumps(context.intent_context, indent=2)}

=== DOCUMENT DETAILS ===
Document: {document_name}
Current Content:
{current_content}

Refinement Instruction:
{instruction}
"""
            messages = [
                ("system", DOCUMENT_REFINER_SYSTEM_PROMPT),
                ("user", user_message)
            ]
            try:
                response = llm.invoke(messages)
                raw_text = response.content.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif raw_text.startswith("```"):
                    lines = raw_text.splitlines()
                    raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:]).strip()
                updated_content = json.loads(raw_text)
                total_tokens = len(raw_text) // 4
            except Exception as full_err:
                logger.error(f"Flat document refinement failed: {full_err}")
                updated_content = current_content

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "DocumentRefinerAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": total_tokens,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "3.0.0"
        }
        
        new_deliverables = context.deliverables.copy()
        new_deliverables[document_name] = {"content": updated_content}
        
        new_metadata = context.metadata.copy()
        new_metadata["refined_document_content"] = updated_content
        
        return context.clone(
            deliverables=new_deliverables,
            metadata=new_metadata
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("workspace_editor", DocumentRefinerAgent())
registry.register("document_refiner", DocumentRefinerAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def refine_document(document_name: str, current_content: Any, instruction: str, workspace: Dict[str, Any]) -> Any:
    """Public wrapper keeping compatibility with UI triggers."""
    ctx = WorkspaceContext.from_dict(workspace)
    refiner = registry.get("document_refiner")
    res_ctx = refiner.execute(ctx, document_name=document_name, current_content=current_content, instruction=instruction)
    return res_ctx.metadata.get("refined_document_content", current_content)
