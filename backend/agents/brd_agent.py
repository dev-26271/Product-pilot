from typing import Dict, Any, List
from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.prompts import BRD_AGENT_SYSTEM_PROMPT

class BRDAgent(BaseDocumentAgent):
    """Agent that generates the Business Requirements Document (BRD)."""
    
    @property
    def required_inputs(self) -> List[str]:
        return ["prd", "business_analysis"]
        
    @property
    def output_schema_keys(self) -> List[str]:
        return ["📈 Market Overview", "💰 Financial Model", "🔒 Compliance & Policy"]
        
    @property
    def system_prompt(self) -> str:
        return BRD_AGENT_SYSTEM_PROMPT
        
    @property
    def agent_name(self) -> str:
        return "BRDAgent"
        
    @property
    def deliverable_key(self) -> str:
        return "Business Requirements Document (BRD)"

# Auto-register agent
registry.register("brd", BRDAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_brd(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("brd").execute(workspace)
        return result_context.deliverables["Business Requirements Document (BRD)"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("brd").execute(ctx)
        return result_context.deliverables["Business Requirements Document (BRD)"]["content"]
