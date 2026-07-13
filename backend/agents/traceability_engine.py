import json
import csv
import logging
from typing import Dict, Any, List, Set, Tuple

logger = logging.getLogger(__name__)

class TraceabilityEngine:
    def __init__(self, workspace: Dict[str, Any]):
        self.workspace = workspace
        # Ensure metadata maps exist to store persistent IDs
        self.metadata = workspace.setdefault("metadata", {})
        self.id_mappings = self.metadata.setdefault("id_mappings", {
            "problem": {},
            "goals": {},
            "features": {},
            "requirements": {},
            "acceptance_criteria": {},
            "epics": {},
            "stories": {},
            "sprints": {},
            "tasks": {}
        })
        self.graph = {
            "nodes": {},  # ID -> {"type": str, "label": str, "details": dict}
            "edges": []   # list of {"source": str, "target": str, "relation": str}
        }
        self.build_graph()

    def get_or_create_id(self, category: str, text: str, prefix: str) -> str:
        """Returns the persistent mapped ID for a text string, or allocates a new sequential ID."""
        if not text:
            return ""
        # Clean text to use as map key
        key = text.strip().lower()
        if key in self.id_mappings[category]:
            return self.id_mappings[category][key]
        
        # Allocate next ID
        allocated_index = len(self.id_mappings[category]) + 1
        allocated_id = f"{prefix}-{allocated_index:03d}"
        self.id_mappings[category][key] = allocated_id
        return allocated_id

    def build_graph(self):
        """Scans workspace deliverables and builds a directed traceability and dependency graph."""
        # 1. Problem Statement (PS-001)
        prob_stmt = ""
        ba = self.workspace.get("business_analysis", {})
        if isinstance(ba, dict):
            prob_stmt = ba.get("problem_statement", "")
        if not prob_stmt:
            intent = self.workspace.get("intent_context", {})
            if isinstance(intent, dict):
                prob_stmt = intent.get("problem_statement", "")
                
        ps_id = ""
        if prob_stmt:
            ps_id = self.get_or_create_id("problem", prob_stmt, "PS")
            self.graph["nodes"][ps_id] = {
                "type": "Problem Statement",
                "label": prob_stmt[:60] + "...",
                "details": {"description": prob_stmt}
            }

        # 2. Business Goals (BG-xxx)
        goals = []
        if isinstance(ba, dict):
            goals = ba.get("goals", [])
            
        bg_ids = []
        for g in goals:
            bg_id = self.get_or_create_id("goals", g, "BG")
            bg_ids.append(bg_id)
            self.graph["nodes"][bg_id] = {
                "type": "Business Goal",
                "label": g[:60] + "...",
                "details": {"description": g}
            }
            if ps_id:
                self.graph["edges"].append({"source": ps_id, "target": bg_id, "relation": "addresses"})

        # 3. Features (FT-xxx)
        features = []
        prd = self.workspace.get("prd", {})
        if isinstance(prd, dict):
            features = prd.get("Core Features", [])
            if not features:
                features = prd.get("✨ Core Features", [])
                
        ft_ids = []
        for f in features:
            f_name = f if isinstance(f, str) else f.get("name", "")
            if not f_name:
                continue
            ft_id = self.get_or_create_id("features", f_name, "FT")
            ft_ids.append(ft_id)
            self.graph["nodes"][ft_id] = {
                "type": "Feature",
                "label": f_name,
                "details": f if isinstance(f, dict) else {"description": f}
            }
            # Heuristic link to business goals
            for bg_id in bg_ids:
                self.graph["edges"].append({"source": bg_id, "target": ft_id, "relation": "owns"})

        # 4. Functional Requirements & AC (FR-xxx, AC-xxx)
        reqs = []
        if isinstance(prd, dict):
            reqs = prd.get("Functional Requirements", [])
            if not reqs:
                reqs = prd.get("⚙️ Functional Requirements", [])
                
        fr_ids = {}
        for r in reqs:
            r_id = r.get("id") or r.get("Requirement ID")
            r_desc = r.get("description") or r.get("Description") or ""
            r_name = r.get("name") or r.get("Name") or r_id or ""
            
            if not r_desc:
                continue
                
            fr_id = self.get_or_create_id("requirements", r_desc, "FR")
            fr_ids[r_id] = fr_id
            fr_ids[r_name] = fr_id
            
            self.graph["nodes"][fr_id] = {
                "type": "Functional Requirement",
                "label": f"{fr_id}: {r_name[:40]}",
                "details": r
            }
            
            # Map requirement back to business goals or features
            bg_target = r.get("business_goal") or r.get("Related Business Goal")
            if bg_target:
                for bg_id in bg_ids:
                    if bg_id in bg_target or self.graph["nodes"][bg_id]["details"]["description"][:10].lower() in bg_target.lower():
                        self.graph["edges"].append({"source": bg_id, "target": fr_id, "relation": "implements"})
                        
            # Map acceptance criteria (AC-xxx)
            ac_list = r.get("acceptance_criteria") or r.get("Acceptance Criteria") or []
            if isinstance(ac_list, str):
                ac_list = [ac_list]
            for ac in ac_list:
                if not ac.strip():
                    continue
                ac_id = self.get_or_create_id("acceptance_criteria", ac, "AC")
                self.graph["nodes"][ac_id] = {
                    "type": "Acceptance Criterion",
                    "label": ac[:50] + "...",
                    "details": {"description": ac}
                }
                self.graph["edges"].append({"source": fr_id, "target": ac_id, "relation": "verifies"})

        # 5. User Stories & Epics (EP-xxx, US-xxx)
        deliverables = self.workspace.get("deliverables", {})
        us_data = deliverables.get("User Stories", {}).get("content", {})
        
        epics = us_data.get("epics", [])
        ep_ids = {}
        for ep in epics:
            ep_title = ep.get("title", "")
            if not ep_title:
                continue
            ep_id = self.get_or_create_id("epics", ep_title, "EP")
            ep_ids[ep.get("id")] = ep_id
            self.graph["nodes"][ep_id] = {
                "type": "Epic",
                "label": ep_title,
                "details": ep
            }
            
        stories = us_data.get("stories", [])
        us_ids = {}
        for st in stories:
            st_title = st.get("title", "")
            if not st_title:
                continue
            us_id = self.get_or_create_id("stories", st_title, "US")
            us_ids[st.get("id")] = us_id
            self.graph["nodes"][us_id] = {
                "type": "User Story",
                "label": f"{us_id}: {st_title[:40]}",
                "details": st
            }
            
            # Link Epic -> owns -> Story
            epic_ref = st.get("epic_id")
            if epic_ref in ep_ids:
                self.graph["edges"].append({"source": ep_ids[epic_ref], "target": us_id, "relation": "owns"})
                
            # Link Story -> implements -> Functional Requirement
            trace_reqs = st.get("traceability", {}).get("functional_requirements", [])
            for tr in trace_reqs:
                if tr in fr_ids:
                    self.graph["edges"].append({"source": us_id, "target": fr_ids[tr], "relation": "implements"})
                elif tr in self.graph["nodes"]:
                    self.graph["edges"].append({"source": us_id, "target": tr, "relation": "implements"})

        # 6. Sprints (SP-xxx)
        sprint_data = deliverables.get("Sprint Backlog", {}).get("content", {})
        sprints = sprint_data.get("sprints", [])
        sp_ids = {}
        for sp in sprints:
            sp_name = sp.get("name", "")
            if not sp_name:
                continue
            sp_id = self.get_or_create_id("sprints", sp_name, "SP")
            sp_ids[sp.get("name")] = sp_id
            self.graph["nodes"][sp_id] = {
                "type": "Sprint",
                "label": sp_name,
                "details": sp
            }
            
            # Link Sprint -> owns -> Stories
            sp_stories = sp.get("stories", [])
            for ss in sp_stories:
                story_ref = ss if isinstance(ss, str) else ss.get("id")
                if story_ref in us_ids:
                    self.graph["edges"].append({"source": sp_id, "target": us_ids[story_ref], "relation": "assigns"})

        # 7. Jira Tasks (JT-xxx)
        jira_data = deliverables.get("Jira Tasks", {}).get("content", {})
        tasks = jira_data.get("tasks", [])
        for task in tasks:
            t_summary = task.get("summary", "")
            if not t_summary:
                continue
            jt_id = self.get_or_create_id("tasks", t_summary, "JT")
            self.graph["nodes"][jt_id] = {
                "type": "Jira Task",
                "label": f"{jt_id}: {t_summary[:40]}",
                "details": task
            }
            
            # Link Jira Task -> implements -> Story
            us_ref = task.get("user_story_id")
            if us_ref in us_ids:
                self.graph["edges"].append({"source": jt_id, "target": us_ids[us_ref], "relation": "resolves"})

    def get_dependencies(self, node_id: str) -> Dict[str, List[str]]:
        """Traverses the directed graph and returns forward/reverse dependencies of the node."""
        forward = []
        reverse = []
        for edge in self.graph["edges"]:
            if edge["source"] == node_id:
                forward.append(edge["target"])
            if edge["target"] == node_id:
                reverse.append(edge["source"])
        return {"forward": forward, "reverse": reverse}

    def calculate_impact(self, edit_instruction: str) -> Dict[str, Any]:
        """Calculates impact level (Low/Medium/High) and identifies list of affected artifacts."""
        from backend.agents.dependency_analyzer import DependencyAnalyzer
        analyzer = DependencyAnalyzer()
        affected = analyzer.analyze(edit_instruction)
        
        # Calculate impact level score
        affected_count = sum(affected.values())
        if affected_count >= 5:
            impact_level = "High"
        elif affected_count >= 2:
            impact_level = "Medium"
        else:
            impact_level = "Low"
            
        # Compile list of affected files/docs
        affected_docs = [k.replace("_", " ").title() for k, v in affected.items() if v]
        
        return {
            "impact_level": impact_level,
            "affected_documents": affected_docs,
            "estimated_regeneration_time": f"{affected_count * 5}s - {affected_count * 8}s"
        }

    def check_coverage(self) -> List[Dict[str, str]]:
        """Validates requirement coverage and reports warnings for any orphaned design elements."""
        warnings = []
        
        # Goals with no features
        goals = [nid for nid, n in self.graph["nodes"].items() if n["type"] == "Business Goal"]
        for g in goals:
            has_feature = any(e["source"] == g and self.graph["nodes"][e["target"]]["type"] == "Feature" for e in self.graph["edges"])
            if not has_feature:
                warnings.append({
                    "category": "Orphan Goal",
                    "item": g,
                    "warning": "This Business Goal has no features mapped to implement it."
                })
                
        # Features with no stories
        features = [nid for nid, n in self.graph["nodes"].items() if n["type"] == "Feature"]
        for f in features:
            # Check if there is a requirements path leading to a user story
            has_story = False
            for e in self.graph["edges"]:
                if e["source"] == f:
                    req_id = e["target"]
                    # If any story maps to this requirement
                    if any(e2["target"] == req_id and self.graph["nodes"][e2["source"]]["type"] == "User Story" for e2 in self.graph["edges"]):
                        has_story = True
            if not has_story:
                warnings.append({
                    "category": "Orphan Feature",
                    "item": f,
                    "warning": "This Feature has no User Stories written to implement it."
                })
                
        # Stories without acceptance criteria
        stories = [nid for nid, n in self.graph["nodes"].items() if n["type"] == "User Story"]
        for s in stories:
            ac_fields = self.graph["nodes"][s]["details"].get("acceptance_criteria", [])
            if not ac_fields:
                warnings.append({
                    "category": "Missing AC",
                    "item": s,
                    "warning": "This User Story contains no acceptance criteria fields."
                })
                
        # Requirements with no KPIs
        reqs = [nid for nid, n in self.graph["nodes"].items() if n["type"] == "Functional Requirement"]
        for r in reqs:
            metrics = self.graph["nodes"][r]["details"].get("metrics") or self.graph["nodes"][r]["details"].get("Success Metric")
            if not metrics:
                warnings.append({
                    "category": "Missing KPI",
                    "item": r,
                    "warning": "This requirement lacks a defined success metric or KPI target."
                })
                
        return warnings

    def export_csv(self) -> str:
        """Generates the Traceability Matrix as a CSV formatted string."""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Source ID", "Source Type", "Source Label", "Target ID", "Target Type", "Target Label", "Relation"])
        
        for edge in self.graph["edges"]:
            src = edge["source"]
            tgt = edge["target"]
            if src in self.graph["nodes"] and tgt in self.graph["nodes"]:
                writer.writerow([
                    src, self.graph["nodes"][src]["type"], self.graph["nodes"][src]["label"],
                    tgt, self.graph["nodes"][tgt]["type"], self.graph["nodes"][tgt]["label"],
                    edge["relation"]
                ])
        return output.getvalue()
