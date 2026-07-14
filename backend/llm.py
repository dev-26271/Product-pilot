import logging
import inspect
import time
import random
import threading
from datetime import datetime
import json
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

INVOCATION_LOG_PATH = "C:/Users/Dev Suri/.gemini/antigravity/brain/adc9e69f-5b0c-4ae6-99cf-c27d5db38958/groq_invocation_log.jsonl"

def strip_metadata_for_llm(data):
    """Recursively removes internal ownership and confidence metadata from JSON to save LLM tokens."""
    if isinstance(data, dict):
        blacklist = {"ownership", "created_at", "last_modified_by", "confidence", "priority_score", "risk_score", "version"}
        return {k: strip_metadata_for_llm(v) for k, v in data.items() if k not in blacklist}
    elif isinstance(data, list):
        return [strip_metadata_for_llm(x) for x in data]
    return data

class CentralizedGroqRequestManager:
    """Thread-safe request manager that queues, rate-limits, and schedules Groq LLM calls."""
    
    def __init__(self):
        self._semaphore = threading.Semaphore(1)
        self._last_request_time = 0.0
        self._min_delay = 2.5  # Shared rate limiter: enforce at least 2.5s between calls
        
    def execute_with_queue(self, messages, invoke_func, agent_name, filename, function_name, *args, **kwargs):
        timestamp = datetime.now().isoformat()
        logger.info(f"[{agent_name}] Queueing Groq request in central manager...")
        
        # 1. Acquire global concurrency lock (limit to 1 active request)
        with self._semaphore:
            # 2. Enforce minimum delay spacing rate-limit
            now = time.perf_counter()
            elapsed = now - self._last_request_time
            if elapsed < self._min_delay:
                sleep_needed = self._min_delay - elapsed
                logger.info(f"Enforcing request spacing: sleeping for {sleep_needed:.2f}s...")
                time.sleep(sleep_needed)
                
            max_retries = 5
            retry_count = 0
            backoff_base = 2.0
            
            while True:
                try:
                    logger.info(f"[{agent_name}] Executing request on Groq endpoint...")
                    start_time = time.perf_counter()
                    
                    response = invoke_func(messages, *args, **kwargs)
                    
                    latency = time.perf_counter() - start_time
                    self._last_request_time = time.perf_counter()
                    
                    # Log and return response
                    metadata = getattr(response, "response_metadata", {})
                    token_usage = metadata.get("token_usage", {})
                    input_tokens = token_usage.get("prompt_tokens", 0)
                    output_tokens = token_usage.get("completion_tokens", 0)
                    
                    # Console logs
                    print("\n" + "="*80)
                    print("[GROQ REQUEST MANAGER EXECUTION]")
                    print(f"  Caller Agent:  {agent_name}")
                    print(f"  Location:      {filename}:{function_name}")
                    print(f"  Input Tokens:  {input_tokens} | Output Tokens: {output_tokens}")
                    print(f"  Latency:       {latency:.4f}s")
                    print(f"  Retry Count:   {retry_count}")
                    print("="*80 + "\n")
                    
                    # Persistent log file
                    try:
                        with open(INVOCATION_LOG_PATH, "a", encoding="utf-8") as log_file:
                            log_file.write(json.dumps({
                                "filename": filename,
                                "function": function_name,
                                "agent_name": agent_name,
                                "timestamp": datetime.now().isoformat(),
                                "input_tokens": input_tokens,
                                "output_tokens": output_tokens,
                                "latency": latency,
                                "retry_count": retry_count
                            }) + "\n")
                    except Exception as log_err:
                        logger.error(f"Failed to write Groq invocation log: {log_err}")
                        
                    return response
                    
                except Exception as e:
                    err_msg = str(e).lower()
                    is_rate_limit = "429" in err_msg or "rate_limit" in err_msg or "rate_limit_exceeded" in err_msg
                    
                    if is_rate_limit and retry_count < max_retries:
                        retry_count += 1
                        
                        # 3. Check for Retry-After header
                        retry_after = None
                        if hasattr(e, "response") and e.response is not None:
                            headers = getattr(e.response, "headers", {})
                            if "retry-after" in headers:
                                try:
                                    retry_after = float(headers["retry-after"])
                                    logger.warning(f"Retry-After header detected: requested delay of {retry_after}s.")
                                except ValueError:
                                    pass
                                    
                        # 4. Fallback to exponential backoff with jitter
                        if retry_after is None:
                            jitter = random.uniform(0.1, 1.0)
                            sleep_time = (backoff_base ** retry_count) + jitter
                        else:
                            sleep_time = retry_after
                            
                        logger.warning(f"[{agent_name}] Groq API Rate Limit (429) encountered. Sleeping {sleep_time:.2f}s (Attempt {retry_count}/{max_retries})...")
                        time.sleep(sleep_time)
                    else:
                        # 5. Graceful fallback logger before raising
                        logger.error(f"[{agent_name}] Groq Request Manager reached terminal state or non-retryable error: {e}")
                        raise e

# Request manager singleton instance
_request_manager = CentralizedGroqRequestManager()

class InstrumentedChatGroq:
    """Wrapper around ChatGroq that routes all requests through the CentralizedGroqRequestManager."""
    
    def __init__(self, base_llm: ChatGroq):
        self._llm = base_llm
        self.model_name = base_llm.model_name
        self.temperature = base_llm.temperature
        self._cache = {}
        
    def invoke(self, messages, *args, **kwargs):
        # Resolve cache key from messages
        try:
            cache_key = json.dumps(messages, default=str)
        except Exception:
            cache_key = str(messages)
            
        if cache_key in self._cache:
            logger.info("Retrieving cached LLM response to save Groq API calls.")
            return self._cache[cache_key]
            
        # Determine caller location using inspection
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename if frame else "unknown"
        function_name = frame.f_code.co_name if frame else "unknown"
        
        # Resolve agent name heuristically
        agent_name = "UnknownAgent"
        if frame and "self" in frame.f_locals:
            caller_self = frame.f_locals["self"]
            if hasattr(caller_self, "agent_name"):
                agent_name = caller_self.agent_name
            else:
                agent_name = caller_self.__class__.__name__
        elif frame and "agent" in frame.f_locals:
            agent_name = str(frame.f_locals["agent"])
            
        # Execute request through central manager
        response = _request_manager.execute_with_queue(
            messages=messages,
            invoke_func=self._llm.invoke,
            agent_name=agent_name,
            filename=filename,
            function_name=function_name,
            *args, **kwargs
        )
        
        # Store in cache
        self._cache[cache_key] = response
        return response
        
    def __getattr__(self, name):
        return getattr(self._llm, name)

# Singleton LLM instance
_llm_instance = None

def get_llm() -> InstrumentedChatGroq:
    """Initializes and returns the ChatGroq model instance singleton wrapper.
    
    Loads GROQ_API_KEY from backend.config only on first call.
    """
    global _llm_instance
    if _llm_instance is None:
        logger.info("Initializing ChatGroq instance singleton")
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not defined in local environment configurations (.env)")
            raise ValueError("GROQ_API_KEY environment variable is missing.")
            
        try:
            # Using standard Llama-3.3-70b-versatile model on Groq for agent task execution
            base_llm = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name="llama-3.3-70b-versatile",
                temperature=0.1
            )
            _llm_instance = InstrumentedChatGroq(base_llm)
        except Exception as e:
            logger.error(f"Failed to initialize ChatGroq client: {e}")
            raise e
    return _llm_instance
