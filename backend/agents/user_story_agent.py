import json
import logging
from typing import Dict, Any, List

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


def _build_user_message(workspace: Dict[str, Any]) -> str:
    """Assembles the full user message from the workspace, including BA and PRD."""

    idea          = workspace.get("idea", "")
    industry      = workspace.get("industry", "Unknown")
    product_type  = workspace.get("product_type", "Unknown")
    audience      = workspace.get("audience", "Unknown")

    # Business Analysis — source of personas and business goals
    business_analysis = workspace.get("business_analysis", {})

    # PRD — primary source of truth for functional requirements
    prd = workspace.get("deliverables", {}).get("Product Requirements Document (PRD)", {})
    prd_content = prd.get("content", prd)  # support both wrapped and raw formats

    return f"""=== PROJECT CONTEXT ===
Product Idea: {idea}
Industry: {industry}
Product Type: {product_type}
Target Audience: {audience}

=== BUSINESS ANALYSIS (source of personas and business goals) ===
{json.dumps(business_analysis, indent=2) if business_analysis else "Not available."}

=== PRODUCT REQUIREMENTS DOCUMENT — PRIMARY SOURCE OF TRUTH ===
{json.dumps(prd_content, indent=2) if prd_content else "Not available."}

=== INSTRUCTIONS ===
Generate Epics and User Stories that directly trace to the Functional Requirements above.
Return ONLY the raw JSON object. No markdown. No prose. No code fences.
Every story MUST include traceability.functional_requirements referencing exact FR IDs from the PRD.
"""


def generate_user_stories(workspace: Dict[str, Any]) -> Dict[str, Any]:
    """Generates structured Agile Epics and User Stories from the workspace context.

    Consumes:
        - workspace["idea"]
        - workspace["business_analysis"]
        - workspace["deliverables"]["Product Requirements Document (PRD)"]

    Returns:
        dict: Validated structured JSON with top-level keys "epics" and "stories".

    Raises:
        ValueError: If the LLM returns invalid JSON or the schema fails critical validation.
        RuntimeError: If the LLM invocation itself fails.
    """
    project_name = workspace.get("name", "Unknown Project")
    logger.info(f"User Story Agent: starting generation for project '{project_name}'")

    prd = workspace.get("deliverables", {}).get("Product Requirements Document (PRD)", {})
    if not prd:
        raise ValueError(
            "User Story Agent requires a generated PRD. "
            "Please generate the PRD first before requesting User Stories."
        )

    # ── Build and invoke LLM ────────────────────────────────────────────────
    user_message = _build_user_message(workspace)
    llm = get_llm()
    messages = [
        ("system", USER_STORY_AGENT_SYSTEM_PROMPT),
        ("user",   user_message),
    ]

    try:
        response = llm.invoke(messages)
        raw_text = response.content.strip()
    except Exception as e:
        logger.error(f"User Story Agent: LLM invocation failed — {e}")
        raise RuntimeError(f"LLM invocation failed: {e}") from e

    # ── Strip fences and parse JSON ─────────────────────────────────────────
    raw_text = _strip_fences(raw_text)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(
            f"User Story Agent: failed to parse LLM response as JSON.\n"
            f"JSONDecodeError: {e}\n"
            f"Raw response (first 1000 chars):\n{raw_text[:1000]}"
        )
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    # ── Top-level schema validation ──────────────────────────────────────────
    if "epics" not in data or not isinstance(data["epics"], list) or len(data["epics"]) == 0:
        raise ValueError("Response missing required 'epics' array or it is empty.")
    if "stories" not in data or not isinstance(data["stories"], list) or len(data["stories"]) == 0:
        raise ValueError("Response missing required 'stories' array or it is empty.")

    # ── Field-level validation (non-fatal: log warnings only) ───────────────
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
    else:
        logger.info("User Story Agent: all epics and stories passed schema validation ✓")

    logger.info(
        f"User Story Agent: generation complete — "
        f"{len(data['epics'])} epic(s), {len(data['stories'])} story(s)"
    )

    return data
