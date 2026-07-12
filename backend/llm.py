import logging
from langchain_groq import ChatGroq
from backend.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

# Singleton LLM instance
_llm_instance = None

def get_llm() -> ChatGroq:
    """Initializes and returns the ChatGroq model instance singleton.
    
    Loads GROQ_API_KEY from backend.config only on first call.
    """
    global _llm_instance
    if _llm_instance is None:
        logger.info("Initializing ChatGroq instance singleton")
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not defined in local environment configurations (.env)")
            raise ValueError("GROQ_API_KEY environment variable is missing.")
            
        try:
            # Using standard Llama-3.1-8b-instant model on Groq for agent task execution
            _llm_instance = ChatGroq(
                groq_api_key=GROQ_API_KEY,
                model_name="llama-3.1-8b-instant",
                temperature=0.1
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatGroq client: {e}")
            raise e
    return _llm_instance
