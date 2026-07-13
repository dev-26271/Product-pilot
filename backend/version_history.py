import copy
from datetime import datetime, timezone
from typing import Dict, Any, List

def compute_workspace_diff(old_ws: Dict[str, Any], new_ws: Dict[str, Any]) -> Dict[str, Any]:
    """Computes the delta change dictionary between two workspace contexts to store them efficiently."""
    delta = {
        "added_or_modified": {},
        "removed": []
    }
    
    fields = ["idea", "intent_context", "business_analysis", "prd", "deliverables"]
    for field in fields:
        old_val = old_ws.get(field)
        new_val = new_ws.get(field)
        
        if old_val != new_val:
            if new_val is None:
                delta["removed"].append(field)
            else:
                delta["added_or_modified"][field] = copy.deepcopy(new_val)
                
    # Selectively diff metadata to avoid storing transient keys
    old_meta = old_ws.get("metadata", {})
    new_meta = new_ws.get("metadata", {})
    filtered_new_meta = {}
    for k, v in new_meta.items():
        if k not in ["version_history", "pending_changes", "pending_approval", "pending_impact", "chat_response"]:
            if old_meta.get(k) != v:
                filtered_new_meta[k] = copy.deepcopy(v)
                
    # Detect removals in metadata
    for k in old_meta.keys():
        if k not in ["version_history", "pending_changes", "pending_approval", "pending_impact", "chat_response"]:
            if k not in new_meta:
                if "removed_metadata" not in delta:
                    delta["removed_metadata"] = []
                delta["removed_metadata"].append(k)
                
    if filtered_new_meta:
        delta["added_or_modified"]["metadata"] = filtered_new_meta
        
    return delta


def apply_delta(ws: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """Applies a delta change dictionary to the base workspace context."""
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
    if not version_history:
        return {}
        
    # Sort version history by version number to be sure
    sorted_history = sorted(version_history, key=lambda x: x.get("version", 1))
    
    # Version 1 is always the full baseline snapshot
    base_ver = sorted_history[0]
    ws = copy.deepcopy(base_ver.get("snapshot") or base_ver)
    
    # Apply deltas sequentially up to target_version_num
    for i in range(1, len(sorted_history)):
        ver = sorted_history[i]
        v_num = ver.get("version", 1)
        if v_num > target_version_num:
            break
            
        delta = ver.get("delta")
        if delta:
            ws = apply_delta(ws, delta)
        elif "snapshot" in ver:
            ws = copy.deepcopy(ver["snapshot"])
            
    # Restore the version history array in metadata so it remains accessible
    ws.setdefault("metadata", {})["version_history"] = copy.deepcopy(version_history)
    return ws
