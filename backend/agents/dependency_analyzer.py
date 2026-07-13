import json
import logging
from typing import Dict, List
from backend.llm import get_llm

logger = logging.getLogger(__name__)

# Key matching definitions for deliverables mapping
DELIVERABLE_KEYWORDS = {
    "business_analysis": ["persona", "customer", "audience", "goal", "kpi", "competitor", "market"],
    "prd": ["feature", "requirement", "fr-", "nfr", "security", "performance", "auth", "payment", "functional", "non-functional"],
    "user_stories": ["story", "user story", "epic", "us-", "ep-"],
    "roadmap": ["roadmap", "timeline", "phase", "quarter", "milestone", "release"],
    "jira": ["jira", "task", "jt-", "ticket", "bug", "issue"],
    "sprint_planning": ["sprint", "backlog", "planning", "sprint backlog"],
    "brd": ["compliance", "policy", "financial", "monetization", "business model", "legal"],
    "srs": ["api", "endpoint", "database", "schema", "technical spec", "system spec"]
}

# Key matching definitions for PRD sections mapping
PRD_SECTION_KEYWORDS = {
    "📋 Executive Summary": ["executive", "summary", "problem", "opportunity", "market", "strategy"],
    "🔭 Product Vision": ["vision", "long-term", "strategic direction"],
    "🎯 Problem Statement": ["problem statement", "pain point", "need"],
    "👥 User Personas": ["persona", "sarah", "david", "user type", "frustration"],
    "📈 Goals & Objectives": ["goal", "objective", "smart", "timeline"],
    "⚙️ Functional Requirements": ["requirement", "functional", "fr-", "auth", "payment", "checkout", "login"],
    "🔒 Non-Functional Requirements": ["nfr", "non-functional", "security", "performance", "scalability", "latency", "uptime"],
    "✨ Core Features": ["feature", "ft-", "video", "thread", "vibe check"],
    "💡 Assumptions": ["assumption", "assume"],
    "🚧 Constraints": ["constraint", "limitation", "boundary"],
    "📊 Success Metrics": ["metric", "success", "dau", "acceptance rate", "retention"],
    "📅 High-Level Roadmap": ["roadmap", "timeline", "phase", "milestone"],
    "❓ Open Questions": ["open question", "unresolved", "clarify"]
}

DEPENDENCY_ANALYZER_PROMPT = """You are an expert software dependency analyzer.
Your task is to analyze the user's product refinement instruction and determine which documents/tabs in the project workspace need to be updated or regenerated.

Tabs/documents in the workspace:
1. business_analysis: Product user personas, market definition, primary user objectives. (Only change if target audience, business model, or domain/industry changes).
2. prd: Product Requirements Document (contains features, functional/non-functional requirements, SMART goals). (Almost always true for any product changes).
3. user_stories: Epics and User Stories. (Changes if functional requirements or features change).
4. roadmap: Product roadmap timeline. (Changes if release plan, phase goals, or high-level milestones change).
5. jira: Jira tasks backlog. (Changes if features or user stories change).
6. sprint_planning: Sprint backlog and sprint tasks. (Changes if sprint goals or user stories change).
7. brd: Business Requirements Document (Market overview, monetization, compliance). (Changes if business models, compliance, or finance changes).
8. srs: Software Requirements Specification (APIs, system metrics, developer specs). (Changes if technical specs, APIs, or database/auth changes).

You MUST respond ONLY with a raw JSON object containing boolean flags (true/false) for each tab.
No markdown code fences, no triple backticks, no conversational text.

Output JSON structure:
{
  "business_analysis": false,
  "prd": true,
  "user_stories": true,
  "roadmap": false,
  "jira": true,
  "sprint_planning": false,
  "brd": false,
  "srs": false
}
"""

class DependencyAnalyzer:
    """Lightweight analyzer to classify refinement instructions and map document dependencies."""
    
    def analyze(self, instruction: str) -> Dict[str, bool]:
        logger.info(f"Analyzing dependencies for instruction: '{instruction[:60]}...'")
        inst_lower = instruction.lower()
        
        # 1. Match deliverables deterministically
        affected_docs = {}
        matched_any = False
        
        for doc, keywords in DELIVERABLE_KEYWORDS.items():
            is_affected = False
            for kw in keywords:
                if kw in inst_lower:
                    is_affected = True
                    matched_any = True
                    break
            affected_docs[doc] = is_affected
            
        # Fallback to LLM only if absolutely no matches are found (ambiguous resolution)
        if not matched_any:
            logger.info("No deterministic keyword matches found. Falling back to LLM dependency analysis.")
            return self._llm_analyze(instruction)
            
        logger.info(f"Deterministic dependency resolution: {affected_docs}")
        return affected_docs

    def analyze_prd_sections(self, instruction: str) -> List[str]:
        """Identifies which specific sections of the PRD are affected by the instruction."""
        inst_lower = instruction.lower()
        affected_sections = []
        
        for section, keywords in PRD_SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw in inst_lower:
                    affected_sections.append(section)
                    break
                    
        if not affected_sections:
            # Fallback: if ambiguous, refine Functional Requirements and Features
            return ["⚙️ Functional Requirements", "✨ Core Features"]
            
        return affected_sections

    def _llm_analyze(self, instruction: str) -> Dict[str, bool]:
        messages = [
            ("system", DEPENDENCY_ANALYZER_PROMPT),
            ("user", f"Refinement Instruction: \"{instruction}\"")
        ]
        
        try:
            llm = get_llm()
            response = llm.invoke(messages)
            raw_text = response.content.strip()
            
            # Clean fences
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_text = "\n".join(lines).strip()
                
            result = json.loads(raw_text)
            
            # Validate types and keys
            validated = {}
            keys = ["business_analysis", "prd", "user_stories", "roadmap", "jira", "sprint_planning", "brd", "srs"]
            for k in keys:
                validated[k] = bool(result.get(k, False))
            return validated
            
        except Exception as e:
            logger.error(f"Dependency analysis failed, falling back to default: {e}")
            return {
                "business_analysis": False,
                "prd": True,
                "user_stories": True,
                "roadmap": False,
                "jira": True,
                "sprint_planning": False,
                "brd": False,
                "srs": False
            }
