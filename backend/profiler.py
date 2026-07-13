import threading
import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)

ENABLE_PROFILING = True

class PerformanceProfiler:
    _local = threading.local()

    @classmethod
    def get_instance(cls) -> "PerformanceProfiler":
        if not hasattr(cls._local, "instance"):
            cls._local.instance = cls()
        return cls._local.instance

    def __init__(self):
        self.timings: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}
        self.sub_timings: Dict[str, float] = {}
        self.sub_start_times: Dict[str, float] = {}

    def start(self, stage_name: str) -> None:
        if not ENABLE_PROFILING:
            return
        self.start_times[stage_name] = time.perf_counter()

    def end(self, stage_name: str) -> None:
        if not ENABLE_PROFILING:
            return
        if stage_name in self.start_times:
            elapsed = time.perf_counter() - self.start_times.pop(stage_name)
            self.timings[stage_name] = elapsed

    def start_sub(self, category: str) -> None:
        if not ENABLE_PROFILING:
            return
        self.sub_start_times[category] = time.perf_counter()

    def end_sub(self, category: str) -> None:
        if not ENABLE_PROFILING:
            return
        if category in self.sub_start_times:
            elapsed = time.perf_counter() - self.sub_start_times.pop(category)
            self.sub_timings[category] = self.sub_timings.get(category, 0.0) + elapsed

    def get_duration(self, stage_name: str) -> float:
        return self.timings.get(stage_name, 0.0)

    def set_duration(self, stage_name: str, duration: float) -> None:
        if not ENABLE_PROFILING:
            return
        self.timings[stage_name] = duration

    def reset(self) -> None:
        self.timings.clear()
        self.start_times.clear()
        self.sub_timings.clear()
        self.sub_start_times.clear()

    def summary(self) -> str:
        if not ENABLE_PROFILING:
            return ""
        
        stages = [
            ("Metadata", "Metadata"),
            ("Intent Extraction", "Intent Extraction"),
            ("RAG Retrieval", "RAG Retrieval"),
            ("Business Analyst", "Business Analyst"),
            ("Product Manager", "Product Manager"),
            ("Validation", "Validation"),
            ("Repair Loop", "Repair Loop"),
            ("Traceability Graph", "Traceability Graph"),
            ("User Stories", "User Stories"),
            ("Roadmap", "Roadmap"),
            ("Jira Tasks", "Jira Tasks"),
            ("Sprint Backlog", "Sprint Backlog")
        ]
        
        # Calculate dynamic overhead to ensure sum matches TOTAL exactly
        total_time = self.timings.get("TOTAL", 0.0)
        
        sum_others = 0.0
        for display_name, stage_key in stages:
            if stage_key != "Metadata":
                sum_others += self.timings.get(stage_key, 0.0)
            
        overhead = max(0.0, total_time - sum_others)
        self.timings["Orchestration Overhead"] = overhead
        
        # Insert overhead to the stages list
        all_stages = stages.copy()
        all_stages.append(("Orchestration Overhead", "Orchestration Overhead"))
        
        lines = []
        lines.append("==============================")
        lines.append("ProductPilot Performance Report")
        lines.append("==============================")
        lines.append("")
        
        for display_name, stage_key in all_stages:
            duration = self.timings.get(stage_key, 0.0)
            dots_count = 22 - len(display_name)
            dots = "." * max(1, dots_count)
            lines.append(f"{display_name} {dots} {duration:.2f} s")
            
        lines.append("")
        lines.append("------------------------------")
        dots_total = 22 - len("TOTAL")
        dots = "." * max(1, dots_total)
        lines.append(f"TOTAL {dots} {total_time:.2f} s")
        
        # Section 2: Fine-Grained Breakdown
        lines.append("")
        lines.append("=========================================")
        lines.append("Detailed Resource Utilization Breakdown")
        lines.append("=========================================")
        
        categories = [
            ("LLM Invocation", "LLM Invocation"),
            ("RAG Loading & Search", "RAG Loading & Search"),
            ("Validation Audits", "Validation Audits"),
            ("Response Parsing", "Response Parsing"),
            ("Prompt Construction", "Prompt Construction"),
            ("Formatting & Markdown", "Formatting & Markdown")
        ]
        
        for display_name, cat_key in categories:
            duration = self.sub_timings.get(cat_key, 0.0)
            pct = (duration / total_time * 100.0) if total_time > 0 else 0.0
            dots_count = 34 - len(display_name)
            dots = "." * max(1, dots_count)
            lines.append(f"{display_name} {dots} {duration:.2f} s  ({pct:.1f}%)")
            
        return "\n".join(lines)
