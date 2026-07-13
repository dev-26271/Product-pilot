import logging
from typing import Dict, Any, List

from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
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


class UserStoryAgent(BaseDocumentAgent):
    """User Story Agent that generates Agile epics and user stories grounded in Intent and PRD."""
    
    @property
    def required_inputs(self) -> List[str]:
        return ["prd", "business_analysis"]
        
    @property
    def output_schema_keys(self) -> List[str]:
        return ["epics", "stories"]
        
    @property
    def system_prompt(self) -> str:
        return USER_STORY_AGENT_SYSTEM_PROMPT
        
    @property
    def agent_name(self) -> str:
        return "UserStoryAgent"
        
    @property
    def deliverable_key(self) -> str:
        return "User Stories"
        
    @property
    def wrap_content(self) -> bool:
        # User stories is cached raw (no content dict wrapper) in deliverables
        return False

    def post_processing(self, parsed_json: Dict[str, Any], context: WorkspaceContext) -> WorkspaceContext:
        all_warnings: List[str] = []
        for idx, epic in enumerate(parsed_json.get("epics", [])):
            all_warnings.extend(_validate_epic(epic, idx))
        for idx, story in enumerate(parsed_json.get("stories", [])):
            all_warnings.extend(_validate_story(story, idx))
            
        if all_warnings:
            logger.warning(
                f"User Story Agent: {len(all_warnings)} validation warning(s) on generated output:\n"
                + "\n".join(f"  ⚠ {w}" for w in all_warnings)
            )
        return context

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
