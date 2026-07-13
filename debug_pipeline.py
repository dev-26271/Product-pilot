"""
ProductPilot Pipeline Diagnostic Instrument
============================================
PURPOSE: Trace every input/output at every stage of the agent pipeline
         to identify where healthcare terminology contaminates non-healthcare projects.

WHAT THIS DOES:
  1. Runs Business Analyst Agent  → logs system prompt, user prompt, RAG chunks, raw LLM response
  2. Runs Product Manager Agent   → logs system prompt, user prompt, RAG chunks, raw LLM response
  3. Runs User Story Agent        → logs system prompt, user prompt, raw LLM response
  4. Scans every logged artifact for healthcare-specific terminology
  5. Produces a contamination source report

IMPORTANT: This script does NOT modify any existing code. It only reads and calls existing functions.
"""

import sys
import os
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# ── Setup paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── Load environment (.env) ──────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# ── Configure logging ────────────────────────────────────────────────────────
LOG_DIR = PROJECT_ROOT / "debug_logs"
LOG_DIR.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"pipeline_trace_{timestamp}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("debug_pipeline")

# ── Healthcare contamination keywords ────────────────────────────────────────
HEALTHCARE_TERMS = [
    "healthcare", "health care", "patient", "doctor", "clinical",
    "medical", "prescri", "diagnos", "hospital", "blood glucose",
    "telemedicine", "telehealth", "EHR", "HL7", "HIPAA",
    "pharmacy", "nurse", "vital sign", "health record",
    "appointment", "symptom", "treatment", "therapy",
    "cardio", "oncolog", "radiology", "lab result",
    "drug", "dosage", "practitioner", "caregiver",
]

def scan_for_contamination(text: str, label: str) -> List[str]:
    """Scans text for healthcare-specific terms. Returns list of (term, context) matches."""
    hits = []
    text_lower = text.lower()
    for term in HEALTHCARE_TERMS:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        for match in pattern.finditer(text):
            start = max(0, match.start() - 60)
            end = min(len(text), match.end() + 60)
            context = text[start:end].replace("\n", " ").strip()
            hits.append(f"  [{label}] Term: '{match.group()}' → ...{context}...")
    return hits


def section_header(title: str) -> str:
    border = "=" * 80
    return f"\n{border}\n  {title}\n{border}\n"


# ==============================================================================
#  TEST INPUT — intentionally NON-healthcare
# ==============================================================================
TEST_IDEA = "A hyper-local food delivery marketplace optimized for eco-friendly drone shipping and zero-waste packaging."
TEST_INPUT = {
    "idea": TEST_IDEA,
    "industry": "Food & Beverage",
    "product_type": "Marketplace",
    "audience": "Urban consumers aged 18-45",
}


def main():
    all_contamination_hits: List[str] = []
    report_lines: List[str] = []

    report_lines.append(section_header("PRODUCTPILOT PIPELINE CONTAMINATION AUDIT"))
    report_lines.append(f"Timestamp     : {datetime.now().isoformat()}")
    report_lines.append(f"Test Idea     : {TEST_IDEA}")
    report_lines.append(f"Test Industry : {TEST_INPUT['industry']}")
    report_lines.append(f"Log File      : {LOG_FILE}")
    report_lines.append("")

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE 1: BUSINESS ANALYST AGENT
    # ══════════════════════════════════════════════════════════════════════════
    report_lines.append(section_header("STAGE 1: BUSINESS ANALYST AGENT"))

    from backend.prompts import BUSINESS_ANALYST_SYSTEM_PROMPT
    from rag import retrieve_business
    from backend.llm import get_llm

    # 1a. System Prompt
    report_lines.append("── 1a. SYSTEM PROMPT ──")
    report_lines.append(BUSINESS_ANALYST_SYSTEM_PROMPT)
    report_lines.append("")
    hits = scan_for_contamination(BUSINESS_ANALYST_SYSTEM_PROMPT, "BA_SYSTEM_PROMPT")
    all_contamination_hits.extend(hits)

    # 1b. RAG Retrieval
    report_lines.append("── 1b. RAG CHUNKS (retrieve_business) ──")
    report_lines.append(f"Query: '{TEST_IDEA}'")
    context_docs = retrieve_business(TEST_IDEA, k=3)
    for i, doc in enumerate(context_docs):
        chunk_text = doc.page_content
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        report_lines.append(f"\n  --- Chunk {i+1} (source: {source}, page: {page}) ---")
        report_lines.append(chunk_text)
        hits = scan_for_contamination(chunk_text, f"BA_RAG_CHUNK_{i+1}")
        all_contamination_hits.extend(hits)
    report_lines.append("")

    # 1c. User Prompt (reconstruct exactly as business_analyst.py does)
    context_str = "\n\n".join([doc.page_content for doc in context_docs])
    ba_user_message = f"""Context:
{context_str}

User Input:
Product Idea: {TEST_INPUT['idea']}
Industry: {TEST_INPUT.get('industry', 'Unknown')}
Product Type: {TEST_INPUT.get('product_type', 'Unknown')}
Audience: {TEST_INPUT.get('audience', 'Unknown')}
"""
    report_lines.append("── 1c. USER PROMPT (sent to LLM) ──")
    report_lines.append(ba_user_message)
    hits = scan_for_contamination(ba_user_message, "BA_USER_PROMPT")
    all_contamination_hits.extend(hits)

    # 1d. Final Messages Array
    ba_messages = [
        ("system", BUSINESS_ANALYST_SYSTEM_PROMPT),
        ("user", ba_user_message),
    ]
    report_lines.append("── 1d. FULL MESSAGES ARRAY (system + user) ──")
    for role, content in ba_messages:
        report_lines.append(f"  [{role}] {content[:200]}...")
    report_lines.append("")

    # 1e. LLM Invocation
    report_lines.append("── 1e. RAW LLM RESPONSE ──")
    llm = get_llm()
    try:
        ba_response = llm.invoke(ba_messages)
        ba_raw = ba_response.content.strip()
        report_lines.append(ba_raw)
        hits = scan_for_contamination(ba_raw, "BA_LLM_RESPONSE")
        all_contamination_hits.extend(hits)
    except Exception as e:
        report_lines.append(f"ERROR: {e}")
        ba_raw = "{}"

    # Parse BA output
    ba_clean = ba_raw
    if ba_clean.startswith("```"):
        lines = ba_clean.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines and lines[-1].startswith("```"): lines = lines[:-1]
        ba_clean = "\n".join(lines).strip()
    try:
        business_analysis = json.loads(ba_clean)
    except json.JSONDecodeError:
        report_lines.append(f"  ⚠ FAILED TO PARSE BA JSON — using empty dict")
        business_analysis = {}

    report_lines.append(f"\n  Parsed BA keys: {list(business_analysis.keys())}")

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE 2: PRODUCT MANAGER (PRD) AGENT
    # ══════════════════════════════════════════════════════════════════════════
    report_lines.append(section_header("STAGE 2: PRODUCT MANAGER (PRD) AGENT"))

    from backend.prompts import PRODUCT_MANAGER_SYSTEM_PROMPT
    from rag import retrieve_product

    # 2a. System Prompt
    report_lines.append("── 2a. SYSTEM PROMPT ──")
    report_lines.append(PRODUCT_MANAGER_SYSTEM_PROMPT)
    report_lines.append("")
    hits = scan_for_contamination(PRODUCT_MANAGER_SYSTEM_PROMPT, "PM_SYSTEM_PROMPT")
    all_contamination_hits.extend(hits)

    # 2b. RAG Retrieval
    # Reconstruct the retrieval query exactly as product_manager.py does
    problem = business_analysis.get("Problem Statement", "")
    goals = " ".join(business_analysis.get("Business Goals", []))
    personas = " ".join([
        f"{p.get('name')} {p.get('role')} {p.get('needs')}"
        for p in business_analysis.get("User Personas", [])
    ])
    pm_retrieval_query = f"{problem} {goals} {personas}".strip()

    report_lines.append("── 2b. RAG CHUNKS (retrieve_product) ──")
    report_lines.append(f"Retrieval Query: '{pm_retrieval_query[:200]}...'")
    pm_context_docs = retrieve_product(pm_retrieval_query, k=3)
    for i, doc in enumerate(pm_context_docs):
        chunk_text = doc.page_content
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "?")
        report_lines.append(f"\n  --- Chunk {i+1} (source: {source}, page: {page}) ---")
        report_lines.append(chunk_text)
        hits = scan_for_contamination(chunk_text, f"PM_RAG_CHUNK_{i+1}")
        all_contamination_hits.extend(hits)
    report_lines.append("")

    # 2c. User Prompt (reconstruct exactly as product_manager.py does)
    pm_context_str = "\n\n".join([doc.page_content for doc in pm_context_docs])
    pm_user_message = f"""Retrieved Product Context:
{pm_context_str}

Business Analysis JSON:
{json.dumps(business_analysis, indent=2)}
"""
    report_lines.append("── 2c. USER PROMPT (sent to LLM) ──")
    report_lines.append(pm_user_message)
    hits = scan_for_contamination(pm_user_message, "PM_USER_PROMPT")
    all_contamination_hits.extend(hits)

    # 2d. LLM Invocation
    pm_messages = [
        ("system", PRODUCT_MANAGER_SYSTEM_PROMPT),
        ("user", pm_user_message),
    ]
    report_lines.append("── 2d. RAW LLM RESPONSE ──")
    try:
        pm_response = llm.invoke(pm_messages)
        pm_raw = pm_response.content.strip()
        report_lines.append(pm_raw)
        hits = scan_for_contamination(pm_raw, "PM_LLM_RESPONSE")
        all_contamination_hits.extend(hits)
    except Exception as e:
        report_lines.append(f"ERROR: {e}")
        pm_raw = "{}"

    # Parse PM output
    pm_clean = pm_raw
    if pm_clean.startswith("```"):
        lines = pm_clean.splitlines()
        if lines[0].startswith("```"): lines = lines[1:]
        if lines and lines[-1].startswith("```"): lines = lines[:-1]
        pm_clean = "\n".join(lines).strip()
    try:
        product_plan = json.loads(pm_clean)
    except json.JSONDecodeError:
        report_lines.append(f"  ⚠ FAILED TO PARSE PM JSON — using empty dict")
        product_plan = {}

    report_lines.append(f"\n  Parsed PM keys: {list(product_plan.keys())}")

    # ══════════════════════════════════════════════════════════════════════════
    #  STAGE 3: USER STORY AGENT
    # ══════════════════════════════════════════════════════════════════════════
    report_lines.append(section_header("STAGE 3: USER STORY AGENT"))

    from backend.prompts import USER_STORY_AGENT_SYSTEM_PROMPT

    # 3a. System Prompt
    report_lines.append("── 3a. SYSTEM PROMPT ──")
    report_lines.append(USER_STORY_AGENT_SYSTEM_PROMPT)
    report_lines.append("")
    hits = scan_for_contamination(USER_STORY_AGENT_SYSTEM_PROMPT, "US_SYSTEM_PROMPT")
    all_contamination_hits.extend(hits)

    # 3b. Build workspace (simulate what output.py does)
    # Build PRD content the same way orchestrator.py does
    func_reqs = product_plan.get("Functional_Requirements", [])
    func_reqs_md = "\n\n".join([
        f"**{r.get('id', '')} — {r.get('title', '')}** (Priority: {r.get('priority', '')})\n"
        f"{r.get('description', '')}\n"
        f"*Acceptance Criteria:* {r.get('acceptance_criteria', '')}"
        for r in func_reqs
    ])
    prd_content = {
        "📋 Executive Summary": product_plan.get("Executive_Summary", ""),
        "🔭 Product Vision": product_plan.get("Product_Vision", ""),
        "🎯 Problem Statement": product_plan.get("Problem_Statement", ""),
        "⚙️ Functional Requirements": func_reqs_md,
    }

    workspace = {
        "name": "Food Delivery Test Project",
        "idea": TEST_IDEA,
        "industry": TEST_INPUT["industry"],
        "product_type": TEST_INPUT["product_type"],
        "audience": TEST_INPUT["audience"],
        "business_analysis": business_analysis,
        "deliverables": {
            "Product Requirements Document (PRD)": {"content": prd_content}
        }
    }

    # Reconstruct user message exactly as user_story_agent.py _build_user_message does
    us_prd = workspace.get("deliverables", {}).get("Product Requirements Document (PRD)", {})
    us_prd_content = us_prd.get("content", us_prd)
    us_user_message = f"""=== PROJECT CONTEXT ===
Product Idea: {workspace.get('idea', '')}
Industry: {workspace.get('industry', 'Unknown')}
Product Type: {workspace.get('product_type', 'Unknown')}
Target Audience: {workspace.get('audience', 'Unknown')}

=== BUSINESS ANALYSIS (source of personas and business goals) ===
{json.dumps(business_analysis, indent=2) if business_analysis else "Not available."}

=== PRODUCT REQUIREMENTS DOCUMENT — PRIMARY SOURCE OF TRUTH ===
{json.dumps(us_prd_content, indent=2) if us_prd_content else "Not available."}

=== INSTRUCTIONS ===
Generate Epics and User Stories that directly trace to the Functional Requirements above.
Return ONLY the raw JSON object. No markdown. No prose. No code fences.
Every story MUST include traceability.functional_requirements referencing exact FR IDs from the PRD.
"""

    report_lines.append("── 3b. USER PROMPT (sent to LLM) ──")
    report_lines.append(us_user_message)
    hits = scan_for_contamination(us_user_message, "US_USER_PROMPT")
    all_contamination_hits.extend(hits)

    # 3c. LLM Invocation
    us_messages = [
        ("system", USER_STORY_AGENT_SYSTEM_PROMPT),
        ("user", us_user_message),
    ]
    report_lines.append("── 3c. RAW LLM RESPONSE ──")
    try:
        us_response = llm.invoke(us_messages)
        us_raw = us_response.content.strip()
        report_lines.append(us_raw)
        hits = scan_for_contamination(us_raw, "US_LLM_RESPONSE")
        all_contamination_hits.extend(hits)
    except Exception as e:
        report_lines.append(f"ERROR: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    #  CONTAMINATION REPORT
    # ══════════════════════════════════════════════════════════════════════════
    report_lines.append(section_header("CONTAMINATION ANALYSIS REPORT"))
    report_lines.append(f"Total healthcare-term matches: {len(all_contamination_hits)}")
    report_lines.append("")

    if all_contamination_hits:
        # Group by source
        sources = {}
        for hit in all_contamination_hits:
            # Extract label from [LABEL]
            match = re.search(r'\[([^\]]+)\]', hit)
            label = match.group(1) if match else "UNKNOWN"
            sources.setdefault(label, []).append(hit)

        report_lines.append("── CONTAMINATION BY SOURCE ──")
        for source_label, source_hits in sources.items():
            report_lines.append(f"\n  📍 {source_label}: {len(source_hits)} hit(s)")
            for h in source_hits[:5]:  # Show up to 5 examples per source
                report_lines.append(f"    {h}")
            if len(source_hits) > 5:
                report_lines.append(f"    ... and {len(source_hits) - 5} more")

        # Determine first contamination point
        report_lines.append("\n── FIRST CONTAMINATION POINT ──")
        stage_order = [
            "BA_SYSTEM_PROMPT", "BA_RAG_CHUNK_1", "BA_RAG_CHUNK_2", "BA_RAG_CHUNK_3",
            "BA_USER_PROMPT", "BA_LLM_RESPONSE",
            "PM_SYSTEM_PROMPT", "PM_RAG_CHUNK_1", "PM_RAG_CHUNK_2", "PM_RAG_CHUNK_3",
            "PM_USER_PROMPT", "PM_LLM_RESPONSE",
            "US_SYSTEM_PROMPT", "US_USER_PROMPT", "US_LLM_RESPONSE",
        ]
        first_source = None
        for stage in stage_order:
            if stage in sources:
                first_source = stage
                break
        if first_source:
            report_lines.append(f"  ⚡ FIRST CONTAMINATION APPEARS AT: {first_source}")
            report_lines.append(f"     ({len(sources[first_source])} healthcare term(s) found here)")
            report_lines.append(f"     This is the ROOT CAUSE of downstream contamination.")
        else:
            report_lines.append(f"  ✅ No contamination detected in any stage.")
    else:
        report_lines.append("  ✅ CLEAN — No healthcare terminology detected in any stage.")

    # ══════════════════════════════════════════════════════════════════════════
    #  KNOWLEDGE BASE AUDIT
    # ══════════════════════════════════════════════════════════════════════════
    report_lines.append(section_header("KNOWLEDGE BASE FILE AUDIT"))
    kb_business = PROJECT_ROOT / "knowledge_base" / "business"
    kb_product = PROJECT_ROOT / "knowledge_base" / "product"

    for label, kb_dir in [("Business KB", kb_business), ("Product KB", kb_product)]:
        report_lines.append(f"\n  📂 {label}: {kb_dir}")
        if kb_dir.exists():
            for f in sorted(kb_dir.glob("*")):
                flag = "  ⚠️ SUSPECT" if any(t in f.name.lower() for t in ["medical", "health", "clinical", "patient", "doctor"]) else ""
                report_lines.append(f"    - {f.name} ({f.stat().st_size:,} bytes){flag}")
        else:
            report_lines.append(f"    (directory not found)")

    # ══════════════════════════════════════════════════════════════════════════
    #  SYSTEM PROMPT AUDIT
    # ══════════════════════════════════════════════════════════════════════════
    report_lines.append(section_header("SYSTEM PROMPT HEALTHCARE TERM AUDIT"))
    from backend import prompts as all_prompts
    prompt_names = [name for name in dir(all_prompts) if name.endswith("_PROMPT")]
    for pname in sorted(prompt_names):
        pval = getattr(all_prompts, pname)
        if isinstance(pval, str):
            hits = scan_for_contamination(pval, pname)
            if hits:
                report_lines.append(f"\n  ⚠️ {pname}: {len(hits)} healthcare term(s)")
                for h in hits:
                    report_lines.append(f"    {h}")
            else:
                report_lines.append(f"  ✅ {pname}: clean")

    # ══════════════════════════════════════════════════════════════════════════
    #  WRITE REPORT
    # ══════════════════════════════════════════════════════════════════════════
    report_text = "\n".join(report_lines)
    REPORT_FILE = LOG_DIR / f"contamination_report_{timestamp}.txt"
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Also write the full trace log
    TRACE_FILE = LOG_DIR / f"full_trace_{timestamp}.txt"
    with open(TRACE_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n{'=' * 80}")
    print(f"  REPORTS SAVED:")
    print(f"    Contamination Report : {REPORT_FILE}")
    print(f"    Full Pipeline Trace  : {TRACE_FILE}")
    print(f"    Python Logging       : {LOG_FILE}")
    print(f"{'=' * 80}")

    # Print summary to console
    print(f"\n  Total contamination hits: {len(all_contamination_hits)}")
    if all_contamination_hits:
        print(f"  ⚡ See report for root cause analysis.")
    else:
        print(f"  ✅ Pipeline is clean.")


if __name__ == "__main__":
    main()
