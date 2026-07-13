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
        
        # 1. Validation of required inputs
        for req in self.required_inputs:
            if req == "prd" and not context.prd:
                raise ValueError(f"{self.agent_name} requires a generated PRD. Please generate PRD first.")
            if req == "business_analysis" and not context.business_analysis:
                raise ValueError(f"{self.agent_name} requires Business Analysis.")
            if req not in ["prd", "business_analysis", "intent_context", "idea"]:
                if req not in context.deliverables:
                    raise ValueError(f"{self.agent_name} requires dependent deliverable '{req}'. Please generate it first.")
                    
        # 2. Prompt construction
        user_message = self.build_user_message(context)
        messages = [
            ("system", self.system_prompt),
            ("user", user_message)
        ]
        
        # 3. LLM invocation
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            # 4. JSON parsing & cleanup
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
                
            parsed_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"{self.agent_name} LLM invoke or JSON parse failed: {e}")
            logger.error(f"{self.agent_name} raw response content: '{raw_text if 'raw_text' in locals() else 'No raw_text'}'")
            raise RuntimeError(f"{self.agent_name} document generation failed: {e}") from e
            
        # 5. Schema validation
        for key in self.output_schema_keys:
            if key not in parsed_json:
                raise ValueError(f"Response from {self.agent_name} is missing mandatory schema key: '{key}'")
                
        # 6. Post-processing & Output formatting
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
            
        return self.post_processing(parsed_json, context.clone(deliverables=new_deliverables)).add_agent_log(log_entry)

    def post_processing(self, parsed_json: Dict[str, Any], context: WorkspaceContext) -> WorkspaceContext:
        """Optional hook for subclasses to perform additional context transformations."""
        return context
