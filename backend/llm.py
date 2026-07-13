import logging
import inspect
from datetime import datetime
import json
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

INVOCATION_LOG_PATH = "C:/Users/Dev Suri/.gemini/antigravity/brain/adc9e69f-5b0c-4ae6-99cf-c27d5db38958/groq_invocation_log.jsonl"

class InstrumentedChatGroq:
    """Wrapper around ChatGroq to instrument invoke calls, print stats, and log usage details."""
    
    def __init__(self, base_llm: ChatGroq):
        self._llm = base_llm
        self.model_name = base_llm.model_name
        self.temperature = base_llm.temperature
        
    def invoke(self, messages, *args, **kwargs):
        # Determine caller filename and function name using inspection
        frame = inspect.currentframe().f_back
        filename = frame.f_code.co_filename if frame else "unknown"
        function_name = frame.f_code.co_name if frame else "unknown"
        
        # Resolve agent name heuristically from frame context
        agent_name = "UnknownAgent"
        if frame and "self" in frame.f_locals:
            caller_self = frame.f_locals["self"]
            if hasattr(caller_self, "agent_name"):
                agent_name = caller_self.agent_name
            else:
                agent_name = caller_self.__class__.__name__
        elif frame and "agent" in frame.f_locals:
            agent_name = str(frame.f_locals["agent"])
            
        timestamp = datetime.now().isoformat()
        
        # Execute the LLM call
        response = self._llm.invoke(messages, *args, **kwargs)
        
        # Parse token counts from langchain response metadata
        metadata = getattr(response, "response_metadata", {})
        token_usage = metadata.get("token_usage", {})
        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)
        
        # Print instrumentation details to stdout
        print("\n" + "="*80)
        print("[GROQ API CALL INSTRUMENTATION]")
        print(f"  Filename:      {filename}")
        print(f"  Function:      {function_name}")
        print(f"  Agent Name:    {agent_name}")
        print(f"  Timestamp:     {timestamp}")
        print(f"  Input Tokens:  {input_tokens}")
        print(f"  Output Tokens: {output_tokens}")
        print("="*80 + "\n")
        
        # Write to chronological log file
        try:
            with open(INVOCATION_LOG_PATH, "a", encoding="utf-8") as log_file:
                log_file.write(json.dumps({
                    "filename": filename,
                    "function": function_name,
                    "agent_name": agent_name,
                    "timestamp": timestamp,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }) + "\n")
        except Exception as log_err:
            logger.error(f"Failed to write Groq invocation log: {log_err}")
            
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
