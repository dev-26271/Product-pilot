import time
import logging
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

# Singleton instance placeholder
_embeddings_instance = None

def get_embeddings() -> HuggingFaceEmbeddings:
    """Exposes the singleton HuggingFaceEmbeddings model instance.
    
    Loads sentence-transformers/all-MiniLM-L6-v2 lazily on the first call
    and caches it for all subsequent requests. Measures initialization time.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        start_time = time.perf_counter()
        logger.info("Initializing HuggingFaceEmbeddings singleton with sentence-transformers/all-MiniLM-L6-v2")
        try:
            _embeddings_instance = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            duration = time.perf_counter() - start_time
            logger.info(f"HuggingFaceEmbeddings singleton initialized in {duration:.4f} seconds.")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise e
    return _embeddings_instance
