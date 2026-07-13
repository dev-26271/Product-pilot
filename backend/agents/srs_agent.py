from typing import Dict, Any, List
from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.prompts import SRS_AGENT_SYSTEM_PROMPT

class SRSAgent(BaseDocumentAgent):
    """Agent that generates the Software Requirements Specification (SRS)."""
    
    @property
    def required_inputs(self) -> List[str]:
        return ["prd"]
        
    @property
    def output_schema_keys(self) -> List[str]:
        return ["⚙️ Functional Requirements", "🔒 Security & System Requirements", "🔌 API Schemas"]
        
    @property
    def system_prompt(self) -> str:
        return SRS_AGENT_SYSTEM_PROMPT
        
    @property
    def agent_name(self) -> str:
        return "SRSAgent"
        
    @property
    def deliverable_key(self) -> str:
        return "Software Requirements Specification (SRS)"

# Auto-register agent
registry.register("srs", SRSAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_srs(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("srs").execute(workspace)
        return result_context.deliverables["Software Requirements Specification (SRS)"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("srs").execute(ctx)
        return result_context.deliverables["Software Requirements Specification (SRS)"]["content"]
