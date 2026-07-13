import copy
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

def sanitize_project_id(project_id: str) -> str:
    import re
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '_', project_id)
    return sanitized

def sanitize_snapshot(workspace: Dict[str, Any]) -> Dict[str, Any]:
    """Clones the workspace dict and strips transient or circular UI variables."""
    ws = copy.deepcopy(workspace)
    meta = ws.setdefault("metadata", {})
    meta.pop("pending_changes", None)
    meta.pop("pending_approval", None)
    meta.pop("pending_impact", None)
    meta.pop("chat_response", None)
    # We also pop version_history from the nested snapshot metadata to avoid massive circular JSON growth!
    meta.pop("version_history", None)
    return ws

def get_changed_deliverables(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> List[str]:
    """Detects which deliverables changed between two workspace states."""
    changed = []
    
    # 1. Compare deliverables
    old_delivs = old_state.get("deliverables", {})
    new_delivs = new_state.get("deliverables", {})
    all_keys = set(old_delivs.keys()) | set(new_delivs.keys())
    for k in all_keys:
        if old_delivs.get(k) != new_delivs.get(k):
            changed.append(k)
            
    # 2. Compare PRD if not already in deliverables list
    if old_state.get("prd") != new_state.get("prd"):
        changed.append("Product Requirements Document (PRD)")
        
    # 3. Compare Business Analysis
    if old_state.get("business_analysis") != new_state.get("business_analysis"):
        changed.append("Business Analysis")
        
    return list(set(changed))

class VersionControl:
    @classmethod
    def create_version(cls, workspace: Dict[str, Any], action: str, summary: str, author: str = "ProductPilot") -> Dict[str, Any]:
        """Creates a new version snapshot and appends it to the project's version history."""
        # 1. Clone workspace dict to avoid mutation side-effects
        ws = copy.deepcopy(workspace)
        metadata = ws.setdefault("metadata", {})
        
        # 2. Get existing version list
        version_history = metadata.setdefault("version_history", [])
        new_version_num = len(version_history) + 1
        
        # 3. Calculate changed deliverables by comparing with previous version's snapshot
        changed_docs = []
        if version_history:
            prev_ver = version_history[-1]
            prev_snapshot = prev_ver.get("snapshot") or {}
            changed_docs = get_changed_deliverables(prev_snapshot, ws)
        else:
            # Baseline version
            changed_docs = ["Product Requirements Document (PRD)", "Business Analysis"]
            
        # 4. Strip circular/transient keys from snapshot
        snapshot = sanitize_snapshot(ws)
        
        # 5. Build version entry
        version_entry = {
            "version": new_version_num,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "author": author,
            "action": action,
            "summary": summary,
            "changed_deliverables": changed_docs,
            # For backwards compatibility with existing UI attributes:
            "description": action,
            "changed_documents": changed_docs,
            "modified_entities": [],
            "validation_status": metadata.get("validation_report", {}),
            "snapshot": snapshot
        }
        
        # 6. Append entry
        version_history.append(version_entry)
        metadata["version_history"] = version_history
        
        # Increment version code for backward compatibility
        metadata["version"] = f"{new_version_num}.0.0"
        metadata["last_updated"] = f"Version {new_version_num} - {action}"
        
        return ws


def apply_delta(ws: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """Applies a delta change dictionary to the base workspace context (backward compatibility)."""
    added = delta.get("added_or_modified", {})
    removed = delta.get("removed", [])
    removed_meta = delta.get("removed_metadata", [])
    
    for k, v in added.items():
        if k == "metadata":
            ws.setdefault("metadata", {}).update(copy.deepcopy(v))
        else:
            ws[k] = copy.deepcopy(v)
            
    for k in removed:
        ws.pop(k, None)
        
    for k in removed_meta:
        if "metadata" in ws:
            ws["metadata"].pop(k, None)
            
    return ws


def rebuild_workspace_version(version_history: List[Dict[str, Any]], target_version_num: int) -> Dict[str, Any]:
    """Rebuilds the complete workspace dictionary at a specific target version number."""
    # Find matching version entry
    ver = next((v for v in version_history if v.get("version") == target_version_num), None)
    if ver and "snapshot" in ver:
        ws = copy.deepcopy(ver["snapshot"])
        # Restore the version history array in metadata so it remains accessible
        ws.setdefault("metadata", {})["version_history"] = copy.deepcopy(version_history)
        return ws
        
    # Fallback to Delta rebuilding if it is an old version format
    if not version_history:
        return {}
    sorted_history = sorted(version_history, key=lambda x: x.get("version", 1))
    base_ver = sorted_history[0]
    ws = copy.deepcopy(base_ver.get("snapshot") or base_ver)
    
    for i in range(1, len(sorted_history)):
        ver = sorted_history[i]
        if ver.get("version", 1) > target_version_num:
            break
        delta = ver.get("delta")
        if delta:
            ws = apply_delta(ws, delta)
        elif "snapshot" in ver:
            ws = copy.deepcopy(ver["snapshot"])
            
    ws.setdefault("metadata", {})["version_history"] = copy.deepcopy(version_history)
    return ws
