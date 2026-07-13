import copy
from typing import Dict, Any, List, Optional

class WorkspaceContext:
    """The canonical project state container for the ProductPilot workspace.
    
    Adheres to the immutability rule: all transformations return a new
    WorkspaceContext instance instead of modifying the existing one in place.
    """
    
    def __init__(self,
                 idea: str = "",
                 intent_context: Optional[Dict[str, Any]] = None,
                 business_analysis: Optional[Dict[str, Any]] = None,
                 prd: Optional[Dict[str, Any]] = None,
                 rag_context: Optional[List[Any]] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 deliverables: Optional[Dict[str, Any]] = None,
                 agent_logs: Optional[List[Dict[str, Any]]] = None):
        self.idea = idea
        self.intent_context = intent_context or {}
        self.business_analysis = business_analysis or {}
        self.prd = prd or {}
        self.rag_context = rag_context or []
        self.metadata = metadata or {}
        self.deliverables = deliverables or {}
        self.agent_logs = agent_logs or []

    def clone(self, **kwargs) -> "WorkspaceContext":
        """Creates a new WorkspaceContext instance, applying the given attribute overrides."""
        new_instance = WorkspaceContext(
            idea=kwargs.get("idea", self.idea),
            intent_context=copy.deepcopy(kwargs.get("intent_context", self.intent_context)),
            business_analysis=copy.deepcopy(kwargs.get("business_analysis", self.business_analysis)),
            prd=copy.deepcopy(kwargs.get("prd", self.prd)),
            rag_context=copy.deepcopy(kwargs.get("rag_context", self.rag_context)),
            metadata=copy.deepcopy(kwargs.get("metadata", self.metadata)),
            deliverables=copy.deepcopy(kwargs.get("deliverables", self.deliverables)),
            agent_logs=copy.deepcopy(kwargs.get("agent_logs", self.agent_logs)),
        )
        return new_instance

    def add_agent_log(self, log_entry: Dict[str, Any]) -> "WorkspaceContext":
        """Returns a new WorkspaceContext instance with a new agent log entry appended."""
        new_logs = copy.deepcopy(self.agent_logs)
        new_logs.append(log_entry)
        return self.clone(agent_logs=new_logs)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the workspace context state into a raw dictionary for JSON/Session storage."""
        return {
            "idea": self.idea,
            "intent_context": self.intent_context,
            "business_analysis": self.business_analysis,
            "prd": self.prd,
            "rag_context": self.rag_context,
            "metadata": self.metadata,
            "deliverables": self.deliverables,
            "agent_logs": self.agent_logs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceContext":
        """Deserializes a WorkspaceContext instance from a raw dictionary with backward compatibility."""
        raw_deliverables = data.get("deliverables", {})
        
        # 1. Parse PRD with backward compatibility
        prd = data.get("prd", {})
        if not prd and "Product Requirements Document (PRD)" in raw_deliverables:
            prd_item = raw_deliverables["Product Requirements Document (PRD)"]
            if isinstance(prd_item, dict):
                prd = prd_item.get("content") or prd_item
                if isinstance(prd, dict) and "content" in prd:
                    prd = prd["content"]
        
        # 2. Parse Business Analysis with backward compatibility
        ba = data.get("business_analysis", {})
        if not ba and "Business Analysis" in raw_deliverables:
            ba_item = raw_deliverables["Business Analysis"]
            if isinstance(ba_item, dict):
                ba = ba_item.get("content") or ba_item
                if isinstance(ba, dict) and "content" in ba:
                    ba = ba["content"]
                    
        # 3. Fallback extraction of BA from PRD if BA is empty but PRD is available
        if not ba and prd:
            goals_raw = []
            if isinstance(prd, dict):
                goals_raw = prd.get("Goals_and_Objectives") or prd.get("🎯 Business Goals") or prd.get("📈 Business Goals") or []
                if isinstance(goals_raw, str):
                    goals_raw = [goals_raw]
            
            personas_raw = []
            if isinstance(prd, dict):
                personas_raw = prd.get("User_Personas") or prd.get("👥 User Personas") or []
                if isinstance(personas_raw, str):
                    personas_raw = [personas_raw]
                    
            ba = {
                "problem_statement": {
                    "id": "PS-001",
                    "text": data.get("idea", (prd.get("Problem_Statement") if isinstance(prd, dict) else None) or "System Problem"),
                },
                "business_goals": [
                    {
                        "id": f"BG-{str(i+1).zfill(3)}",
                        "goal": g if isinstance(g, str) else g.get("goal", str(g)),
                        "smart": {"specific": "", "measurable": "", "achievable": "", "relevant": "", "time_bound": ""},
                    }
                    for i, g in enumerate(goals_raw)
                ] if isinstance(goals_raw, list) else [],
                "user_personas": [
                    {
                        "id": f"PE-{str(i+1).zfill(3)}",
                        "name": p.get("name", f"Persona {i+1}") if isinstance(p, dict) else str(p),
                        "role": p.get("role", "") if isinstance(p, dict) else "",
                    }
                    for i, p in enumerate(personas_raw)
                ] if isinstance(personas_raw, list) else []
            }

        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {
                "name": data.get("name"),
                "industry": data.get("industry"),
                "product_type": data.get("product_type"),
                "audience": data.get("audience"),
                "status": data.get("metadata", "Active")
            }
            
        return cls(
            idea=data.get("idea", ""),
            intent_context=data.get("intent_context", {}),
            business_analysis=ba,
            prd=prd,
            rag_context=data.get("rag_context", []),
            metadata=metadata,
            deliverables=raw_deliverables,
            agent_logs=data.get("agent_logs", []),
        )

