import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Set

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.agents.traceability_engine import TraceabilityEngine

logger = logging.getLogger(__name__)

IMPACT_ANALYSIS_SYSTEM_PROMPT = """You are a Principal Software Architect and Change Management Analyst.
Your task is to analyze a proposed product modification instruction, identify the directly affected entities in the workspace, and evaluate the impact.

You MUST respond ONLY with a raw JSON object. No markdown, no backticks, no conversational text.

The JSON schema must be structured exactly as follows:
{
  "directly_affected_entity_ids": ["BG-001", "PE-002"],
  "breaking_changes": ["Description of potential breaking change"],
  "warnings": ["Warning statement about risk or complexity"],
  "recommendations": ["Actionable design or regeneration recommendation"],
  "confidence": 0.95
}

Rules:
1. Match the refinement instruction against the list of current entities to identify which ones are directly modified, added, or deleted.
2. If an entity is directly mentioned or its core functionality is changed, include its ID.
3. Do not invent entities. Only reference IDs from the provided list.
4. If no existing entities are directly affected (e.g., adding an entirely new goal or feature), return an empty list for directly_affected_entity_ids.
"""


class ImpactAnalysisAgent(BaseAgent):
    """Impact Analysis Agent — performs Change Impact Analysis across the workspace."""

    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing ImpactAnalysisAgent...")
        start_time = time.perf_counter()

        instruction = kwargs.get("instruction", "")
        if not instruction:
            logger.warning("No instruction provided for change impact analysis.")
            return context

        # 1. Build entity graph using TraceabilityEngine
        engine = TraceabilityEngine(context.to_dict())
        nodes = engine.graph.get("nodes", {})
        edges = engine.graph.get("edges", [])

        # Build list of active entities for LLM context
        entities_list = []
        for nid, node in nodes.items():
            entities_list.append({
                "id": nid,
                "type": node.get("type", ""),
                "label": node.get("label", "")
            })

        user_prompt = f"""Proposed Modification:
"{instruction}"

Active Entities in Workspace:
{json.dumps(entities_list, indent=2)}
"""

        # 2. Call LLM to detect directly affected entities
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", IMPACT_ANALYSIS_SYSTEM_PROMPT),
            ("user", user_prompt)
        ]

        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:]).strip()
            analysis_json = json.loads(raw_text)
        except Exception as e:
            logger.error(f"Impact Analysis LLM call failed: {e}")
            analysis_json = {
                "directly_affected_entity_ids": [],
                "breaking_changes": [],
                "warnings": ["Failed to parse impact analysis response from LLM."],
                "recommendations": ["Review the changes manually."],
                "confidence": 0.50
            }

        directly_affected = analysis_json.get("directly_affected_entity_ids", [])
        
        # 3. Traverse downstream dependencies to find cascading affected entities
        downstream_map = _build_downstream_map(edges)
        all_affected_ids = _traverse_dependencies(downstream_map, directly_affected)

        # 4. Compile detailed affected entities info
        affected_entities = []
        affected_doc_keys = set()
        
        doc_prefix_map = {
            "PS": "business_analysis",
            "BG": "business_analysis",
            "PE": "business_analysis",
            "FT": "prd",
            "FR": "prd",
            "AC": "prd",
            "EP": "user_stories",
            "US": "user_stories",
            "SP": "roadmap",
            "JT": "jira",
            "Sprint": "sprint_planning"
        }

        # Human readable document names
        doc_names_map = {
            "business_analysis": "Business Analysis",
            "prd": "Product Requirements Document (PRD)",
            "user_stories": "User Stories",
            "roadmap": "Product Roadmap",
            "jira": "Jira Tasks",
            "sprint_planning": "Sprint Backlog",
            "brd": "Business Requirements Document (BRD)",
            "srs": "Software Requirements Specification (SRS)"
        }

        # If it's a structural or wide change, suggest wider document updates
        # If user is adding something new, we might not have direct IDs, so map via doc classification
        if not directly_affected:
            from backend.agents.dependency_analyzer import DependencyAnalyzer
            doc_analyzer = DependencyAnalyzer()
            affected_docs_flags = doc_analyzer.analyze(instruction)
            for k, v in affected_docs_flags.items():
                if v:
                    affected_doc_keys.add(k)
        else:
            for aid in all_affected_ids:
                if aid in nodes:
                    node = nodes[aid]
                    affected_entities.append({
                        "id": aid,
                        "type": node.get("type", ""),
                        "name": node.get("label", "")
                    })
                    # Map to document key
                    prefix = aid.split("-")[0] if "-" in aid else ""
                    doc_key = doc_prefix_map.get(prefix)
                    if doc_key:
                        affected_doc_keys.add(doc_key)

        # Build list of human readable affected documents
        affected_documents = [doc_names_map[k] for k in affected_doc_keys if k in doc_names_map]
        if not affected_documents:
            # Safe default
            affected_documents = ["Product Requirements Document (PRD)"]
            affected_doc_keys.add("prd")

        # Convert back to flags dict for apply logic
        affected_flags = {k: (k in affected_doc_keys) for k in doc_names_map.keys()}

        # 5. Estimate AI costs & regeneration time
        entity_count = len(affected_entities) or 1
        est_tokens = entity_count * 800 + 3000
        usd_cost = round(est_tokens * 0.000015, 4)
        
        regeneration_time = f"{len(affected_documents) * 5}s"
        severity = "High" if entity_count > 5 else "Medium" if entity_count > 2 else "Low"

        # Build final pending impact analysis dict
        pending_impact = {
            "instruction": instruction,
            "affected": affected_flags,  # document flags dict for apply logic
            "affected_entities": affected_entities,
            "affected_documents": affected_documents,
            "breaking_changes": analysis_json.get("breaking_changes", []),
            "warnings": analysis_json.get("warnings", []),
            "recommendations": analysis_json.get("recommendations", []),
            "estimated_regeneration_cost": {
                "tokens": est_tokens,
                "usd_cost": usd_cost
            },
            "estimated_regeneration_time": regeneration_time,
            "severity": severity,
            "confidence": analysis_json.get("confidence", 0.90)
        }

        new_metadata = context.metadata.copy()
        new_metadata["pending_impact"] = pending_impact
        # Store entity graph in metadata context
        new_metadata["entity_graph"] = engine.metadata.get("entity_graph", {})

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        log_entry = {
            "agent": "ImpactAnalysisAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "confidence": pending_impact["confidence"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "3.0.0"
        }

        return context.clone(metadata=new_metadata).add_agent_log(log_entry)


# ---------------------------------------------------------------------------
# Dependency Traversal Helpers
# ---------------------------------------------------------------------------

def _build_downstream_map(edges: List[Dict[str, str]]) -> Dict[str, List[str]]:
    """Builds a downstream adjacency list based on relationship directionality."""
    downstream = {}
    for edge in edges:
        u = edge["source"]
        v = edge["target"]
        
        src_prefix = u.split("-")[0] if "-" in u else ""
        tgt_prefix = v.split("-")[0] if "-" in v else ""
        
        # Upstream -> Downstream flow mapping:
        # PS -> BG -> FT -> FR -> AC
        # FR -> US -> JT
        # EP -> US
        
        is_reversed = False
        # If target prefix is upstream of source prefix, reverse direction
        if (tgt_prefix, src_prefix) in [("FR", "US"), ("US", "JT"), ("FR", "FT")]:
            is_reversed = True
            
        if is_reversed:
            downstream.setdefault(v, []).append(u)
        else:
            downstream.setdefault(u, []).append(v)
            
    return downstream


def _traverse_dependencies(downstream_map: Dict[str, List[str]], start_entities: List[str]) -> Set[str]:
    """Performs depth-first search traversal to collect all downstream dependent entity IDs."""
    visited = set()
    queue = list(start_entities)
    while queue:
        curr = queue.pop(0)
        if curr not in visited:
            visited.add(curr)
            for n in downstream_map.get(curr, []):
                if n not in visited:
                    queue.append(n)
    return visited


# Register agent singleton
registry.register("impact_analysis", ImpactAnalysisAgent())
