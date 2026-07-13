import json
import time
import logging
from datetime import datetime
from abc import abstractmethod
from typing import Dict, Any, List

from backend.agent_registry import BaseAgent
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm

logger = logging.getLogger(__name__)

class BaseDocumentAgent(BaseAgent):
    """Abstract Base Class for all document-generation agents in ProductPilot.
    
    Provides standardized context loading, validation, execution metrics,
    JSON parsing, and serialization.
    """
    
    @property
    @abstractmethod
    def required_inputs(self) -> List[str]:
        """List of required WorkspaceContext fields (e.g., ['prd', 'business_analysis'])."""
        pass
        
    @property
    @abstractmethod
    def output_schema_keys(self) -> List[str]:
        """List of required JSON keys that must be present in the LLM response."""
        pass
        
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt containing output schema format and generation instructions."""
        pass
        
    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Identifying name of the agent for logging metrics (e.g., 'UserStoryAgent')."""
        pass
        
    @property
    @abstractmethod
    def deliverable_key(self) -> str:
        """The key in context.deliverables where the compiled output is cached."""
        pass

    @property
    def wrap_content(self) -> bool:
        """If True, wraps output JSON in {"content": data} for legacy UI compatibility."""
        return True

    def build_user_message(self, context: WorkspaceContext) -> str:
        """Standardized user context injection prompt."""
        sections = []
        sections.append("=== INTENT CONTEXT (Canonical Source of Truth) ===")
        sections.append(json.dumps(context.intent_context, indent=2))
        
        if "business_analysis" in self.required_inputs:
            sections.append("=== BUSINESS ANALYSIS ===")
            sections.append(json.dumps(context.business_analysis, indent=2))
            
        if "prd" in self.required_inputs:
            sections.append("=== PRODUCT REQUIREMENTS DOCUMENT ===")
            sections.append(json.dumps(context.prd, indent=2))
            
        # Add dependent deliverables if any are required
        for req in self.required_inputs:
            if req not in ["prd", "business_analysis", "intent_context", "idea"]:
                sections.append(f"=== DEPENDENT DELIVERABLE: {req} ===")
                sections.append(json.dumps(context.deliverables.get(req, {}), indent=2))
                
        return "\n\n".join(sections)

    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info(f"Executing {self.agent_name}...")
        start_time = time.perf_counter()
        
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()
        
        # 1. Validation of required inputs
        profiler.start_sub("Validation Audits")
        for req in self.required_inputs:
            if req == "prd" and not context.prd:
                profiler.end_sub("Validation Audits")
                raise ValueError(f"{self.agent_name} requires a generated PRD. Please generate PRD first.")
            if req == "business_analysis" and not context.business_analysis:
                profiler.end_sub("Validation Audits")
                raise ValueError(f"{self.agent_name} requires Business Analysis.")
            if req not in ["prd", "business_analysis", "intent_context", "idea"]:
                if req not in context.deliverables:
                    profiler.end_sub("Validation Audits")
                    raise ValueError(f"{self.agent_name} requires dependent deliverable '{req}'. Please generate it first.")
        profiler.end_sub("Validation Audits")
                    
        # 2. Prompt construction
        profiler.start_sub("Prompt Construction")
        mode = kwargs.get("mode", "generate")
        instruction = kwargs.get("instruction", "")
        
        if mode == "update" and self.deliverable_key in context.deliverables:
            existing_doc = context.deliverables[self.deliverable_key]
            existing_content = existing_doc.get("content", existing_doc)
            
            user_message = f"""=== EXISTING DOCUMENT ({self.deliverable_key}) ===
{json.dumps(existing_content, indent=2)}

=== REFINEMENT INSTRUCTION ===
{instruction}

Your task is to refine and update the existing document based on the refinement instruction.
Output the complete updated document matching the exact schema structure of the original document. Output ONLY the raw JSON representation. Do not include markdown code fences, backticks, or conversational text.
"""
            system_prompt = f"You are a Technical Product Manager. Update this {self.deliverable_key} deliverable incrementally based on the user instructions. Do not rewrite unchanged elements. Maintain exact keys and structure."
            messages = [
                ("system", system_prompt),
                ("user", user_message)
            ]
        else:
            user_message = self.build_user_message(context)
            messages = [
                ("system", self.system_prompt),
                ("user", user_message)
            ]
        profiler.end_sub("Prompt Construction")
        
        # 3. LLM invocation
        profiler.start_sub("LLM Invocation")
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        
        raw_text = ""
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            profiler.end_sub("LLM Invocation")
            
            # 4. JSON parsing & cleanup
            profiler.start_sub("Response Parsing")
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
            try:
                parsed_json = json.loads(raw_text)
            except Exception as parse_err:
                cleaned = raw_text.strip()
                if cleaned.startswith("{") and not cleaned.endswith("}"):
                    try:
                        parsed_json = json.loads(cleaned + "}")
                        logger.info(f"{self.agent_name}: successfully repaired JSON by appending closing brace.")
                    except Exception:
                        raise parse_err
                else:
                    raise parse_err
            profiler.end_sub("Response Parsing")
        except Exception as e:
            profiler.end_sub("LLM Invocation")
            # Safe clean for response parsing timer if active
            profiler.end_sub("Response Parsing")
            logger.error(f"{self.agent_name} LLM invoke or JSON parse failed: {e}")
            logger.error(f"{self.agent_name} raw response content: '{raw_text if 'raw_text' in locals() else 'No raw_text'}'")
            
            # Safe fallback construction
            parsed_json = {}
            for key in self.output_schema_keys:
                if key in ["epics", "stories", "tasks", "phases", "business_goals", "user_personas", "Functional_Requirements", "Core_Features"]:
                    parsed_json[key] = []
                else:
                    parsed_json[key] = f"Draft {key} generated as placeholder due to parsing error."
            if not self.output_schema_keys:
                # Use default fallback matching agent name
                parsed_json = {
                    self.deliverable_key: f"Draft {self.deliverable_key} created."
                }
            
        # 5. Schema validation
        profiler.start_sub("Validation Audits")
        for key in self.output_schema_keys:
            if key not in parsed_json:
                profiler.end_sub("Validation Audits")
                raise ValueError(f"Response from {self.agent_name} is missing mandatory schema key: '{key}'")
        profiler.end_sub("Validation Audits")
                
        # 6. Post-processing & Output formatting
        profiler.start_sub("Formatting & Markdown")
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # 7. Agent logging
        log_entry = {
            "agent": self.agent_name,
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        new_deliverables = context.deliverables.copy()
        if self.wrap_content:
            new_deliverables[self.deliverable_key] = {"content": parsed_json}
        else:
            new_deliverables[self.deliverable_key] = parsed_json
            
        res_ctx = self.post_processing(parsed_json, context.clone(deliverables=new_deliverables)).add_agent_log(log_entry)
        profiler.end_sub("Formatting & Markdown")
        return res_ctx

    def post_processing(self, parsed_json: Dict[str, Any], context: WorkspaceContext) -> WorkspaceContext:
        """Optional hook for subclasses to perform additional context transformations."""
        return context
