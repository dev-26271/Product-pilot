import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext
from backend.agents.base_document_agent import BaseDocumentAgent
from backend.agents.entity_schema import (
    validate_entity_envelope, validate_domain_fields,
    JIRA_TASK_REQUIRED, VALID_TASK_TYPES, FIBONACCI_POINTS
)
from backend.prompts import JIRA_AGENT_SYSTEM_PROMPT

import logging
logger = logging.getLogger(__name__)


class JiraAgent(BaseDocumentAgent):
    """Jira Agent — produces canonical structured Jira Task entities."""

    @property
    def required_inputs(self) -> List[str]:
        return ["prd"]

    @property
    def output_schema_keys(self) -> List[str]:
        return []

    @property
    def system_prompt(self) -> str:
        return JIRA_AGENT_SYSTEM_PROMPT

    @property
    def agent_name(self) -> str:
        return "JiraAgent"

    @property
    def deliverable_key(self) -> str:
        return "Jira Tasks"

    def build_user_message(self, context: WorkspaceContext) -> str:
        base_msg = super().build_user_message(context)
        raw_us = context.deliverables.get("User Stories", {})
        if isinstance(raw_us, dict) and "stories" in raw_us:
            user_stories_context = raw_us.get("stories", [])
        elif isinstance(raw_us, dict) and "content" in raw_us:
            user_stories_context = raw_us["content"]
        else:
            user_stories_context = []
        extra_msg = f"""
=== USER STORIES ===
{json.dumps(user_stories_context, indent=2) if user_stories_context else "Not generated yet. Base tasks on the PRD only."}

Current UTC timestamp: {datetime.now(timezone.utc).isoformat()}
"""
        return base_msg + "\n" + extra_msg

    def post_processing(self, parsed_json: Dict[str, Any], context: WorkspaceContext) -> WorkspaceContext:
        """Validate entities and format tasks into markdown grouped by type."""
        tasks = parsed_json.get("tasks", [])

        # Handle legacy string-blob output from old prompt
        if not tasks:
            legacy_text = (
                parsed_json.get("\U0001f3ab Jira Tasks")
                or parsed_json.get("Jira Tasks", "")
            )
            if legacy_text:
                logger.warning("JiraAgent: received legacy string output; storing as plain content.")
                new_deliverables = context.deliverables.copy()
                new_deliverables[self.deliverable_key] = {
                    "content": {"\U0001f3ab Jira Tasks": legacy_text},
                    "entities": {"tasks": []},
                }
                return context.clone(deliverables=new_deliverables)

        # Validate + audit
        all_warnings = []
        types_seen = set()
        for task in tasks:
            tid = task.get("id", "JT-?")
            all_warnings.extend(validate_entity_envelope(task, tid))
            all_warnings.extend(validate_domain_fields(task, JIRA_TASK_REQUIRED, tid))
            # Type enum check
            ttype = task.get("type", "")
            if ttype not in VALID_TASK_TYPES:
                all_warnings.append(f"{tid}: invalid type '{ttype}' — must be one of {VALID_TASK_TYPES}")
            else:
                types_seen.add(ttype)
            # Fibonacci story points
            sp = task.get("estimate", {}).get("story_points")
            if sp is not None and sp not in FIBONACCI_POINTS:
                all_warnings.append(f"{tid}: story_points={sp} is not Fibonacci")

        missing_types = VALID_TASK_TYPES - types_seen
        if missing_types:
            all_warnings.append(f"JiraAgent: missing task types: {missing_types}")

        if all_warnings:
            logger.warning(f"JiraAgent: {len(all_warnings)} entity warnings:\n" + "\n".join(f"  \u26a0 {w}" for w in all_warnings))

        tasks_md = _format_tasks_as_markdown(tasks)

        new_deliverables = context.deliverables.copy()
        new_deliverables[self.deliverable_key] = {
            "content": {"\U0001f3ab Jira Tasks": tasks_md},
            "entities": {"tasks": tasks},
        }
        return context.clone(deliverables=new_deliverables)


def _format_tasks_as_markdown(tasks: List[Dict[str, Any]]) -> str:
    # Group by type
    by_type: Dict[str, List] = {}
    for task in tasks:
        ttype = task.get("type", "Other")
        by_type.setdefault(ttype, []).append(task)

    TYPE_ICONS = {
        "Frontend": "\U0001f5a5\ufe0f", "Backend": "\u2699\ufe0f", "Database": "\U0001f4be",
        "API": "\U0001f517", "Testing": "\U0001f9ea", "DevOps": "\U0001f680", "Documentation": "\U0001f4dd",
    }

    parts = []
    for ttype in ["Frontend", "Backend", "Database", "API", "Testing", "DevOps", "Documentation"]:
        group = by_type.get(ttype, [])
        if not group:
            continue
        icon = TYPE_ICONS.get(ttype, "")
        section = [f"## {icon} {ttype}"]
        for task in group:
            tid = task.get("id", "JT-?")
            title = task.get("title", "")
            desc = task.get("description", "")
            priority = task.get("priority", "")
            est = task.get("estimate", {})
            hours = est.get("hours", "?")
            sp = est.get("story_points", "?")
            deps = task.get("dependencies", [])
            deps_str = ", ".join(deps) if deps else "None"
            ac_list = task.get("acceptance_criteria", [])
            ac_str = "\n".join(f"  - {a}" for a in ac_list) if ac_list else "  - N/A"
            trace = task.get("traceability", {})
            impl = ", ".join(trace.get("implements", []))
            section.append(
                f"\n**{tid} \u2014 {title}** | Priority: {priority} | {hours}h / {sp}SP\n"
                f"{desc}\n"
                f"- *Acceptance Criteria:*\n{ac_str}\n"
                f"- *Dependencies:* {deps_str}\n"
                f"- *Implements:* {impl or 'N/A'}"
            )
        parts.append("\n".join(section))
    return "\n\n---\n\n".join(parts)


# Auto-register agent
registry.register("jira", JiraAgent())


# -- Backwards Compatible Public Wrapper --
def generate_jira_tasks(workspace: Any) -> Dict[str, Any]:
    if isinstance(workspace, WorkspaceContext):
        result_context = registry.get("jira").execute(workspace)
        return result_context.deliverables["Jira Tasks"]["content"]
    else:
        ctx = WorkspaceContext.from_dict(workspace)
        result_context = registry.get("jira").execute(ctx)
        return result_context.deliverables["Jira Tasks"]["content"]
