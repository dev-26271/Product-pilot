"""
test_user_story_agent.py

Standalone verification script for the production-grade User Story Agent.
Run from the prd_generator project root:
    python test_user_story_agent.py

Validates:
  ✓ Valid JSON output
  ✓ Multiple Epics
  ✓ Multiple Stories
  ✓ Traceability exists and is non-empty
  ✓ Story Points exist and are valid Fibonacci numbers
  ✓ Dependencies field exists (array)
  ✓ Status exists
  ✓ Epic has business_value and release
  ✓ Output is consumable by downstream agents (Roadmap, Sprint, Jira)
"""

import json
import logging
import sys

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("test_user_story_agent")

FIBONACCI = {1, 2, 3, 5, 8, 13}

# ── Rich mock workspace with a realistic PRD ─────────────────────────────────
MOCK_WORKSPACE = {
    "name": "Healthcare AI Platform",
    "idea": (
        "Build a healthcare platform where patients can consult doctors online, "
        "manage prescriptions, schedule appointments, and receive AI-powered "
        "health recommendations."
    ),
    "industry":     "Healthcare",
    "product_type": "Mobile Application",
    "audience":     "B2C",
    "business_analysis": {
        "Problem Statement": (
            "Patients with chronic conditions lack real-time access to clinical "
            "guidance, leading to delayed care and poor health outcomes."
        ),
        "Business Goals": [
            "Reduce critical care response intervals by 65% within 6 months",
            "Onboard 1,000 board-certified physicians in the first quarter",
            "Achieve a patient CSAT score of 92% or higher within 12 months",
        ],
        "User Personas": [
            {
                "name": "Dr. Sarah",
                "role": "Board-certified General Practitioner",
                "needs": "Clean telemetry dashboards, automated threshold alerts, EHR export."
            },
            {
                "name": "Patient David",
                "role": "Chronic condition patient (Type-2 Diabetes)",
                "needs": "Lightweight mobile glucose tracking, on-demand video consultations, prescription refills."
            },
        ],
    },
    "deliverables": {
        "Product Requirements Document (PRD)": {
            "content": {
                "📋 Executive Summary": (
                    "A telehealth platform enabling secure, real-time consultations "
                    "between patients and board-certified physicians with AI-assisted "
                    "recommendations and wearable device integration."
                ),
                "⚙️ Functional Requirements": json.dumps([
                    {
                        "id": "FR-001",
                        "title": "Secure Video Consultation",
                        "description": "Patients must be able to initiate end-to-end encrypted video calls with their assigned physician.",
                        "priority": "High",
                        "acceptance_criteria": "Video call initiates within 3 seconds; AES-256 encryption applied throughout session."
                    },
                    {
                        "id": "FR-002",
                        "title": "Wearable Telemetry Sync",
                        "description": "The platform must ingest glucose readings from paired wearable devices via BLE in real time.",
                        "priority": "High",
                        "acceptance_criteria": "Readings sync within 10 seconds of device measurement; data persisted in FHIR-compliant format."
                    },
                    {
                        "id": "FR-003",
                        "title": "AI Health Recommendations",
                        "description": "The system must generate personalised health insights and alerts based on telemetry trends using an ML model.",
                        "priority": "Medium",
                        "acceptance_criteria": "Recommendation generated within 60 seconds of abnormal reading; physician approval required before patient delivery."
                    },
                    {
                        "id": "FR-004",
                        "title": "Prescription Management",
                        "description": "Physicians must be able to issue, renew, and cancel digital prescriptions within the platform.",
                        "priority": "High",
                        "acceptance_criteria": "Prescription transmitted to partner pharmacy within 5 minutes; patient receives SMS/push notification."
                    },
                    {
                        "id": "FR-005",
                        "title": "Appointment Scheduling",
                        "description": "Patients must be able to browse physician availability and book appointments with conflict detection.",
                        "priority": "Medium",
                        "acceptance_criteria": "Booking confirmed within 2 seconds; calendar invite sent to both parties."
                    },
                ], indent=2),
                "📊 Success Metrics": (
                    "- DAU growth of 15% MoM\n"
                    "- Average consultation wait time < 5 minutes\n"
                    "- Patient retention rate > 80% at 90 days"
                ),
            }
        }
    }
}


def run_checks(data: dict) -> list[str]:
    """Returns a list of failure messages. Empty list = all checks passed."""
    failures = []

    # ── Top-level keys ────────────────────────────────────────────────────────
    if not isinstance(data.get("epics"), list) or len(data["epics"]) == 0:
        failures.append("FAIL: 'epics' is missing or empty")

    if not isinstance(data.get("stories"), list) or len(data["stories"]) == 0:
        failures.append("FAIL: 'stories' is missing or empty")

    if failures:
        return failures  # abort early — nothing else to check

    # ── Epics validation ──────────────────────────────────────────────────────
    epic_ids = set()
    for i, epic in enumerate(data["epics"]):
        eid = epic.get("id", f"Epic[{i}]")
        epic_ids.add(eid)
        if not epic.get("business_value"):
            failures.append(f"FAIL: {eid} missing 'business_value'")
        if not epic.get("release"):
            failures.append(f"FAIL: {eid} missing 'release'")
        if not epic.get("status"):
            failures.append(f"FAIL: {eid} missing 'status'")

    if len(data["epics"]) < 2:
        failures.append(f"FAIL: expected >= 2 epics, got {len(data['epics'])}")

    # ── Stories validation ────────────────────────────────────────────────────
    if len(data["stories"]) < 4:
        failures.append(f"FAIL: expected >= 4 stories, got {len(data['stories'])}")

    for i, story in enumerate(data["stories"]):
        sid = story.get("id", f"Story[{i}]")

        # Status
        if not story.get("status"):
            failures.append(f"FAIL: {sid} missing 'status'")

        # Story points
        estimate = story.get("estimate")
        if not isinstance(estimate, dict):
            failures.append(f"FAIL: {sid} 'estimate' is not a dict")
        else:
            sp = estimate.get("story_points")
            if sp is None:
                failures.append(f"FAIL: {sid} missing 'estimate.story_points'")
            elif sp not in FIBONACCI:
                failures.append(f"FAIL: {sid} story_points={sp} not Fibonacci")
            if not estimate.get("complexity"):
                failures.append(f"FAIL: {sid} missing 'estimate.complexity'")

        # Dependencies (must be a list, can be empty)
        if not isinstance(story.get("dependencies"), list):
            failures.append(f"FAIL: {sid} 'dependencies' must be an array")

        # Acceptance criteria
        ac = story.get("acceptance_criteria")
        if not isinstance(ac, list) or len(ac) < 2:
            failures.append(f"FAIL: {sid} must have >= 2 acceptance_criteria")

        # Traceability
        trace = story.get("traceability")
        if not isinstance(trace, dict):
            failures.append(f"FAIL: {sid} 'traceability' is not a dict")
        else:
            frs = trace.get("functional_requirements")
            if not isinstance(frs, list) or len(frs) == 0:
                failures.append(f"FAIL: {sid} 'traceability.functional_requirements' is empty or missing")

    return failures


def main() -> None:
    print("\n" + "=" * 65)
    print("  ProductPilot — User Story Agent Verification Script")
    print("=" * 65)

    from backend.agents.user_story_agent import generate_user_stories

    print("\n[Step 1] Invoking User Story Agent...")
    try:
        result = generate_user_stories(MOCK_WORKSPACE)
    except Exception as e:
        print(f"\n✗ AGENT FAILED: {e}")
        sys.exit(1)

    print("\n[Step 2] Running schema validations...")
    failures = run_checks(result)

    print(f"\n  Epics   : {len(result.get('epics', []))}")
    print(f"  Stories : {len(result.get('stories', []))}")

    if failures:
        print(f"\n✗ {len(failures)} check(s) FAILED:")
        for f in failures:
            print(f"  • {f}")
        sys.exit(1)
    else:
        print("\n✓ All checks passed!\n")

    print("[Step 3] Full structured output:\n")
    print(json.dumps(result, indent=2))

    print("\n" + "=" * 65)
    print("  VERIFICATION COMPLETE ✓")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
