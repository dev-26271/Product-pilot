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

    def start(self, stage_name: str) -> None:
        if not ENABLE_PROFILING:
            return
        self.start_times[stage_name] = time.perf_counter()

    def end(self, stage_name: str) -> None:
        if not ENABLE_PROFILING:
            return
        if stage_name in self.start_times:
            elapsed = time.perf_counter() - self.start_times[stage_name]
            self.timings[stage_name] = elapsed

    def get_duration(self, stage_name: str) -> float:
        return self.timings.get(stage_name, 0.0)

    def set_duration(self, stage_name: str, duration: float) -> None:
        if not ENABLE_PROFILING:
            return
        self.timings[stage_name] = duration

    def reset(self) -> None:
        self.timings.clear()
        self.start_times.clear()

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
            ("User Stories", "User Stories"),
            ("Roadmap", "Roadmap"),
            ("Jira Tasks", "Jira Tasks"),
            ("Sprint Backlog", "Sprint Backlog")
        ]
        
        lines = []
        lines.append("==============================")
        lines.append("ProductPilot Performance Report")
        lines.append("==============================")
        lines.append("")
        
        total_time = 0.0
        for display_name, stage_key in stages:
            duration = self.timings.get(stage_key, 0.0)
            total_time += duration
            dots_count = 22 - len(display_name)
            dots = "." * max(1, dots_count)
            lines.append(f"{display_name} {dots} {duration:.2f} s")
            
        lines.append("")
        lines.append("------------------------------")
        total_override = self.timings.get("TOTAL")
        final_total = total_override if total_override is not None else total_time
        dots_total = 22 - len("TOTAL")
        dots = "." * max(1, dots_total)
        lines.append(f"TOTAL {dots} {final_total:.2f} s")
        
        return "\n".join(lines)
