import os
import json
import time
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any

from backend.agent_registry import registry
from backend.workspace_context import WorkspaceContext


# Force importing of agents package to trigger self-registration hooks
import backend.agents

logger = logging.getLogger(__name__)

ENABLE_SEMANTIC_VALIDATION = False

# Fast local keyword rules for metadata pre-parsing (latency-saving)
INDUSTRY_PATTERNS = {
    "Healthcare": r"\b(health|medical|clinic|doctor|patient|hospital|nurse|pharmacy|clinical|telemed)\b",
    "Finance": r"\b(finance|bank|wallet|pay|transaction|invest|budget|crypt|ledger|stock)\b",
    "Education": r"\b(student|teach|tutor|learn|class|school|course|education|academy)\b",
    "Retail": r"\b(retail|store|shop|e-commerce|checkout|merchant|grocery)\b",
    "Food & Beverage": r"\b(food|delivery|restaurant|beverage|eat|drone shipping|zero-waste)\b",
    "Logistics": r"\b(warehouse|inventory|shipping|transport|logistics|supply|reorder)\b",
    "Agriculture": r"\b(farm|agriculture|soil|crop|harvest|irrigate)\b",
    "Travel": r"\b(travel|flight|hotel|trip|vacation|booking)\b",
    "Real Estate": r"\b(property|house|rent|real estate|apartment|broker)\b",
    "HR": r"\b(hr|employee|hire|recruit|payroll|talent)\b",
    "Legal": r"\b(legal|law|contract|attorney|sign)\b",
    "Entertainment": r"\b(game|movie|music|video|stream|entertainment|play)\b",
}

PRODUCT_TYPE_PATTERNS = {
    "SaaS Platform": r"\b(saas|cloud platform|dashboard|portal|multi-tenant)\b",
    "Mobile App": r"\b(mobile app|ios|android|phone app|tablet app)\b",
    "AI Assistant": r"\b(ai assistant|chatbot|llm|copilot|tutor|gpt)\b",
    "Marketplace": r"\b(marketplace|platform|delivery|matching|vendor|ecommerce)\b",
    "Dashboard": r"\b(dashboard|analytics|reporting|telemetry|visualizer)\b",
    "Internal Tool": r"\b(internal tool|operator tool|back-office|admin tool)\b",
    "API Platform": r"\b(api platform|developer portal|endpoint|integration)\b",
    "CRM": r"\b(crm|customer relations|lead tracking|contact manager)\b",
}

AUDIENCE_PATTERNS = {
    "B2B": r"\b(b2b|business to business|vendor|merchant|operator|business partner)\b",
    "B2C": r"\b(b2c|consumer|end user|customer|shopper|individual|patient|student)\b",
    "Enterprise": r"\b(enterprise|corporate|bank|hospital|large-scale|security-conscious)\b",
    "Internal": r"\b(internal|staff|employee|operations|back-office)\b",
    "Government": r"\b(government|agency|public sector|municipal)\b",
}


def _fast_regex_parse(idea: str) -> Dict[str, str]:
    """Helper that runs quick regex-based keyword matches to classify an idea instantly."""
    idea_lower = idea.lower()
    inferred = {}
    
    # 1. Industry match
    for ind, pattern in INDUSTRY_PATTERNS.items():
        if re.search(pattern, idea_lower):
            inferred["industry"] = ind
            break
            
    # 2. Product type match
    for ptype, pattern in PRODUCT_TYPE_PATTERNS.items():
        if re.search(pattern, idea_lower):
            inferred["product_type"] = ptype
            break
            
    # 3. Audience match
    for aud, pattern in AUDIENCE_PATTERNS.items():
        if re.search(pattern, idea_lower):
            inferred["audience"] = aud
            break
            
    return inferred


def infer_project_metadata(idea: str) -> Dict[str, str]:
    """Infers industry, product_type, and audience from a product idea.
    
    First runs a zero-latency fast keyword pre-parser, falling back to a lightweight LLM call
    if matches are inconclusive. Always returns a confidence-score structured outcome.
    """
    from backend.profiler import PerformanceProfiler
    profiler = PerformanceProfiler.get_instance()
    profiler.start("Metadata")
    try:
        logger.info("Running metadata inference...")
        
        # Try zero-latency fast parser first
        fast_inferred = _fast_regex_parse(idea)
        if len(fast_inferred) == 3:
            logger.info(f"Fast parser achieved 100% resolution: {fast_inferred}")
            return fast_inferred
            
        # Fall back to lightweight LLM classifier for remaining fields
        from backend.llm import get_llm
        
        profiler.start_sub("Prompt Construction")
        system_prompt = """You are a product classifier. Given a product idea, return a JSON object with exactly three keys:
{
  "industry": "<one of: Healthcare, Finance, Education, Retail, Logistics, Travel, Real Estate, HR, Legal, Entertainment, Food & Beverage, Agriculture, Government, Technology, Other>",
  "product_type": "<one of: SaaS Platform, Mobile App, AI Assistant, Marketplace, Dashboard, Internal Tool, API Platform, Enterprise Software, CRM, Productivity Tool>",
  "audience": "<one of: B2B, B2C, Enterprise, Internal, Government>"
}

Rules:
- Return ONLY the raw JSON object. No markdown, no backticks, no explanation.
- Pick the single best match for each field based on the product idea.
- If uncertain, choose the closest reasonable option.
"""
        user_message = f"Product idea: {idea}\nFast Pre-parsed defaults: {fast_inferred}"
        profiler.end_sub("Prompt Construction")
        
        raw = ""
        try:
            profiler.start_sub("LLM Invocation")
            llm = get_llm()
            response = llm.invoke([
                ("system", system_prompt),
                ("user", user_message),
            ])
            raw = response.content.strip()
            profiler.end_sub("LLM Invocation")
            
            profiler.start_sub("Response Parsing")
            # Strip code fences if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            
            data = json.loads(raw)
            profiler.end_sub("Response Parsing")
            
            profiler.start_sub("Formatting & Markdown")
            # Combine fast parser results with LLM results
            final_inferred = {
                "industry": fast_inferred.get("industry") or data.get("industry", "Other"),
                "product_type": fast_inferred.get("product_type") or data.get("product_type", "SaaS Platform"),
                "audience": fast_inferred.get("audience") or data.get("audience", "B2C"),
            }
            logger.info(f"Metadata inference completed successfully: {final_inferred}")
            profiler.end_sub("Formatting & Markdown")
            return final_inferred
        except Exception as e:
            profiler.end_sub("LLM Invocation")
            profiler.end_sub("Response Parsing")
            profiler.end_sub("Formatting & Markdown")
            logger.warning(f"Lightweight LLM metadata classification failed, using fallbacks: {e}")
            return {
                "industry": fast_inferred.get("industry", "Other"),
                "product_type": fast_inferred.get("product_type", "SaaS Platform"),
                "audience": fast_inferred.get("audience", "B2C"),
            }
    finally:
        profiler.end("Metadata")


class OrchestrationStrategy(ABC):
    """Abstract Strategy interface for routing the multi-agent pipeline execution."""
    
    @abstractmethod
    def execute(self, payload: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Runs the specific orchestration workflow logic."""
        pass


class PythonLocalStrategy(OrchestrationStrategy):
    """Runs the PRD-only pipeline locally using BaseAgent execution loops on WorkspaceContext."""
    
    def execute(self, payload: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        logger.info("Executing PythonLocalStrategy (multi-agent context pipeline)...")
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()
        profiler.start("TOTAL")
        start_time = time.perf_counter()
        
        project_data = payload.get("project", payload)
        idea = project_data.get("idea", "")
        project_name = project_data.get("name") or (" ".join(idea.split()[:2]) + " Project")
        
        # UI selection overrides if manually configured
        pre_parsed_meta = {
            "project_id": project_name,
            "industry": project_data.get("industry"),
            "product_type": project_data.get("product_type"),
            "audience": project_data.get("audience"),
            "risk_analysis": project_data.get("risk_analysis", True)
        }
        
        # 1. Initialize WorkspaceContext
        context = WorkspaceContext(
            idea=idea,
            metadata=pre_parsed_meta.copy()
        )
        
        # --- KNOWLEDGE GROUNDING LAYER (ENTERPRISE RAG) ---
        from backend.agents.retrieval_service import RetrievalService
        from rag.embeddings import get_embeddings
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
        import rag.retriever
        from pathlib import Path
        
        profiler.start("RAG Retrieval")
        logger.info(f"Initializing orchestrator-owned RAG grounding context for project '{project_name}'...")
        rag_service = RetrievalService(use_reranker=True)
        
        # Retrieve context (automatically loads, merges, and caches index inside RetrievalService)
        grounding_chunks = rag_service.get_grounding_context(idea, project_id=project_name)
        
        # Populate context and pre-register in retrieve module
        context.rag_context = grounding_chunks
        lc_docs = [
            Document(page_content=chunk["content"], metadata=chunk["metadata"])
            for chunk in grounding_chunks
        ]
        rag.retriever.ACTIVE_GROUNDING_CONTEXT = lc_docs
        logger.info(f"Grounded workspace context with {len(lc_docs)} chunks.")
        profiler.end("RAG Retrieval")
        
        # 2. Step 1: Intent Extraction Agent
        if progress_callback: progress_callback('Intent Extraction', 'running')
        intent_agent = registry.get("intent_extractor")
        profiler.start("Intent Extraction")
        context = intent_agent.execute(context, pre_parsed_metadata=pre_parsed_meta)
        profiler.end("Intent Extraction")
        if progress_callback: progress_callback('Intent Extraction', 'done')
        
        # 3. Step 2: Business Analyst Agent
        if progress_callback: progress_callback('Business Analysis', 'running')
        ba_agent = registry.get("business_analyst")
        profiler.start("Business Analyst")
        context = ba_agent.execute(context)
        profiler.end("Business Analyst")
        if progress_callback: progress_callback('Business Analysis', 'done')
        
        # 4. Step 3: Product Manager Agent
        if progress_callback: progress_callback('PRD Generation', 'running')
        pm_agent = registry.get("product_manager")
        profiler.start("Product Manager")
        context = pm_agent.execute(context)
        profiler.end("Product Manager")
        if progress_callback: progress_callback('PRD Generation', 'done')
        
        # 5. Step 4: Deterministic Python Validation & Optional Semantic Audit
        if progress_callback: progress_callback('Validation', 'running')
        from backend.validation.validator import DeterministicValidator
        validator = DeterministicValidator()
        
        t_val_start = time.perf_counter()
        profiler.start_sub("Validation Audits")
        val_report = validator.validate(context)
        profiler.end_sub("Validation Audits")
        
        # Auto-fix simple issues if score < 0.95
        repair_duration = 0.0
        if val_report.get("score", 1.0) < 0.95 and val_report.get("repair_actions"):
            logger.info(f"PRD score ({val_report.get('score')}) below threshold 0.95. Executing python auto-fixes: {val_report.get('repair_actions')}")
            t_repair_start = time.perf_counter()
            context = validator.auto_fix(context, val_report["repair_actions"])
            repair_duration = time.perf_counter() - t_repair_start
            
            # Re-run validator
            val_report = validator.validate(context)
            logger.info(f"Validator re-run score after auto-fixes: {val_report.get('score')}")
            
        context.metadata["validation_report"] = val_report
        validation_duration = time.perf_counter() - t_val_start
        
        # Optional Semantic Validation Agent (default False)
        if ENABLE_SEMANTIC_VALIDATION:
            val_agent = registry.get("semantic_validation_agent")
            t_sem_start = time.perf_counter()
            context = val_agent.execute(context)
            validation_duration += (time.perf_counter() - t_sem_start)
            val_report = context.metadata.get("validation_report", val_report)
            
        if progress_callback: progress_callback('Validation', 'done')
        profiler.set_duration("Validation", validation_duration)
        profiler.set_duration("Repair Loop", repair_duration)
               # Build and update entity_graph in context metadata
        from backend.agents.traceability_engine import TraceabilityEngine
        profiler.start("Traceability Graph")
        try:
            engine = TraceabilityEngine(context.to_dict())
            context.metadata["entity_graph"] = engine.metadata.get("entity_graph", {})
            context.metadata["id_mappings"] = engine.metadata.get("id_mappings", {})
            logger.info("TraceabilityEngine successfully built entity graph for workspace context.")
        except Exception as e:
            logger.error(f"Failed to build initial entity graph: {e}")
        profiler.end("Traceability Graph")
  
        # 6. Step 5: Planning Analysis calculation (deterministic)
        try:
            from backend.agents.entity_schema import calculate_planning_analysis
            context.metadata["planning_analysis"] = calculate_planning_analysis(context)
            logger.info("Deterministic planning analysis computed successfully.")
        except Exception as e:
            logger.error(f"Failed to calculate deterministic planning analysis: {e}")
            
        total_duration = time.perf_counter() - start_time
        logger.info(f"Initial Multi-Agent PRD pipeline completed in {total_duration:.4f} seconds.")
        profiler.end("TOTAL")
        
        # Generate summary report first to calculate and populate Orchestration Overhead
        summary_report = profiler.summary()
        
        # Save timings inside context
        context.performance.update(profiler.timings)
        
        # Print clean timing report automatically to standard output
        print(summary_report)
        
        # Return serializable dict output maintaining backwards compatibility with UI
        if progress_callback: progress_callback('Ready', 'done')
        
        res_dict = context.to_dict()
        res_dict["success"] = True
        res_dict["data"] = context.deliverables
        res_dict["business_analysis"] = context.business_analysis
        
        return res_dict



def generate_prd(payload: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
    """Executes the PRD-only initial generation using the local Python orchestration pipeline."""
    logger.info("Executing local Python orchestration pipeline...")
    strategy = PythonLocalStrategy()
    try:
        return strategy.execute(payload, progress_callback=progress_callback)
    except Exception as e:
        logger.error(f"Orchestration execution failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
