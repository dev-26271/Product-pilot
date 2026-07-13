import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

from backend.agent_registry import BaseAgent, registry
from backend.workspace_context import WorkspaceContext
from backend.llm import get_llm
from backend.prompts import USER_STORY_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ── Allowed enumerated values for validation ──────────────────────────────────
VALID_EPIC_STATUSES   = {"Draft", "Ready", "In Progress", "Done"}
VALID_STORY_STATUSES  = {"To Do", "In Progress", "Blocked", "Done"}
VALID_PRIORITIES      = {"Critical", "High", "Medium", "Low"}
VALID_COMPLEXITIES    = {"Low", "Medium", "High"}
VALID_RISKS           = {"Low", "Medium", "High"}
VALID_RELEASES        = {"MVP", "Phase 1", "Phase 2", "Phase 3"}
FIBONACCI_POINTS      = {1, 2, 3, 5, 8, 13}


def _strip_fences(text: str) -> str:
    """Removes markdown code fences (```json ... ```) that some models return."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _validate_epic(epic: Dict[str, Any], idx: int) -> List[str]:
    """Validates a single epic dict and returns a list of warning strings."""
    warnings: List[str] = []
    eid = epic.get("id", f"Epic[{idx}]")

    for field in ("id", "title", "description", "business_value", "release", "status"):
        if not epic.get(field):
            warnings.append(f"{eid}: missing required field '{field}'")

    if epic.get("status") and epic["status"] not in VALID_EPIC_STATUSES:
        warnings.append(f"{eid}: invalid status '{epic['status']}' — must be one of {VALID_EPIC_STATUSES}")

    if epic.get("release") and epic["release"] not in VALID_RELEASES:
        warnings.append(f"{eid}: invalid release '{epic['release']}' — must be one of {VALID_RELEASES}")

    return warnings


def _validate_story(story: Dict[str, Any], idx: int) -> List[str]:
    """Validates a single story dict and returns a list of warning strings."""
    warnings: List[str] = []
    sid = story.get("id", f"Story[{idx}]")

    # Mandatory scalar fields
    for field in ("id", "epic_id", "feature", "title", "persona", "action", "value", "priority", "risk", "status"):
        if not story.get(field):
            warnings.append(f"{sid}: missing required field '{field}'")

    # Enum validations
    if story.get("priority") and story["priority"] not in VALID_PRIORITIES:
        warnings.append(f"{sid}: invalid priority '{story['priority']}'")
    if story.get("status") and story["status"] not in VALID_STORY_STATUSES:
        warnings.append(f"{sid}: invalid status '{story['status']}'")
    if story.get("risk") and story["risk"] not in VALID_RISKS:
        warnings.append(f"{sid}: invalid risk '{story['risk']}'")

    # Estimate block
    estimate = story.get("estimate")
    if not isinstance(estimate, dict):
        warnings.append(f"{sid}: 'estimate' must be an object with 'story_points' and 'complexity'")
    else:
        sp = estimate.get("story_points")
        if sp is None:
            warnings.append(f"{sid}: 'estimate.story_points' is missing")
        elif sp not in FIBONACCI_POINTS:
            warnings.append(f"{sid}: story_points={sp} is not a valid Fibonacci number {FIBONACCI_POINTS}")
        if estimate.get("complexity") and estimate["complexity"] not in VALID_COMPLEXITIES:
            warnings.append(f"{sid}: invalid complexity '{estimate['complexity']}'")

    # Acceptance criteria — must be a non-empty list
    ac = story.get("acceptance_criteria")
    if not isinstance(ac, list) or len(ac) < 2:
        warnings.append(f"{sid}: 'acceptance_criteria' must be a list with at least 2 items")

    # Traceability — functional_requirements is mandatory
    trace = story.get("traceability")
    if not isinstance(trace, dict):
        warnings.append(f"{sid}: 'traceability' must be an object")
    else:
        frs = trace.get("functional_requirements")
        if not isinstance(frs, list) or len(frs) == 0:
            warnings.append(f"{sid}: 'traceability.functional_requirements' is mandatory and must be non-empty")

    # Dependencies — must be a list (can be empty)
    if not isinstance(story.get("dependencies"), list):
        warnings.append(f"{sid}: 'dependencies' must be an array (use [] if none)")

    # Labels — must be a list
    if not isinstance(story.get("labels"), list):
        warnings.append(f"{sid}: 'labels' must be an array")

    return warnings


class UserStoryAgent(BaseAgent):
    """User Story Agent that generates Agile epics and user stories grounded in Intent and PRD."""
    
    def execute(self, context: WorkspaceContext, **kwargs) -> WorkspaceContext:
        logger.info("Executing UserStoryAgent...")
        start_time = time.perf_counter()
        
        # Verify PRD is populated
        if not context.prd:
            raise ValueError(
                "User Story Agent requires a generated PRD. "
                "Please generate the PRD first before requesting User Stories."
            )
            
        user_message = f"""=== INTENT CONTEXT (Canonical Source of Truth) ===
{json.dumps(context.intent_context, indent=2)}

=== BUSINESS ANALYSIS ===
{json.dumps(context.business_analysis, indent=2)}

=== PRODUCT REQUIREMENTS DOCUMENT ===
{json.dumps(context.prd, indent=2)}
"""
        
        llm = get_llm()
        model_name = getattr(llm, "model_name", "llama-3.1-8b-instant")
        messages = [
            ("system", USER_STORY_AGENT_SYSTEM_PROMPT),
            ("user", user_message)
        ]
        
        try:
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            # Clean fences
            raw_text = _strip_fences(raw_text)
            data = json.loads(raw_text)
        except Exception as e:
            logger.error(f"User Story Agent LLM invoke or parse failed: {e}")
            raise RuntimeError(f"User Story generation failed: {e}") from e
            
        # Validate schema keys
        if "epics" not in data or not isinstance(data["epics"], list) or len(data["epics"]) == 0:
            raise ValueError("Response missing required 'epics' array or it is empty.")
        if "stories" not in data or not isinstance(data["stories"], list) or len(data["stories"]) == 0:
            raise ValueError("Response missing required 'stories' array or it is empty.")
            
        # Field-level validation warnings
        all_warnings: List[str] = []
        for idx, epic in enumerate(data["epics"]):
            all_warnings.extend(_validate_epic(epic, idx))
        for idx, story in enumerate(data["stories"]):
            all_warnings.extend(_validate_story(story, idx))
            
        if all_warnings:
            logger.warning(
                f"User Story Agent: {len(all_warnings)} validation warning(s) on generated output:\n"
                + "\n".join(f"  ⚠ {w}" for w in all_warnings)
            )
            
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        # Log entry
        log_entry = {
            "agent": "UserStoryAgent",
            "model": model_name,
            "latency_ms": duration_ms,
            "tokens": len(raw_text) // 4 if 'raw_text' in locals() else 0,
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0"
        }
        
        # Store in deliverables list under 'User Stories' key directly (no wrapping)
        new_deliverables = context.deliverables.copy()
        new_deliverables["User Stories"] = data
        
        return context.clone(
            deliverables=new_deliverables
        ).add_agent_log(log_entry)

# Auto-register agent
registry.register("user_story", UserStoryAgent())


# ── Backwards Compatible Public Wrapper ───────────────────────────────────────
def generate_user_stories(workspace: Any) -> Dict[str, Any]:
    """Public wrapper to keep backwards compatibility with the lazy UI loader."""
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("user_story").execute(workspace)
        return result_context.deliverables["User Stories"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("user_story").execute(ctx)
        return result_context.deliverables["User Stories"]
