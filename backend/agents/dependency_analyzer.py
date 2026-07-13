import json
import logging
from typing import Dict
from backend.llm import get_llm

logger = logging.getLogger(__name__)

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
{{
  "business_analysis": false,
  "prd": true,
  "user_stories": true,
  "roadmap": false,
  "jira": true,
  "sprint_planning": false,
  "brd": false,
  "srs": false
}}
"""

class DependencyAnalyzer:
    """Lightweight analyzer to classify refinement instructions and map document dependencies."""
    
    def analyze(self, instruction: str) -> Dict[str, bool]:
        logger.info(f"Analyzing dependencies for instruction: '{instruction[:60]}...'")
        
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
            logger.error(f"Dependency analysis failed, falling back to all-true: {e}")
            # Safe default: update prd and related downstream documents
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
