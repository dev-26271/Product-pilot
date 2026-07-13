import time
import logging
from pathlib import Path
from typing import List
from functools import lru_cache
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)

# Orchestrator-owned active grounding context (avoids individual agent-level queries)
ACTIVE_GROUNDING_CONTEXT: List[Document] = []

@lru_cache(maxsize=2)
def _load_vectorstore(domain: str) -> FAISS:
    """Loads the FAISS vectorstore for a given domain from disk."""
    base_dir = Path(__file__).resolve().parent.parent
    index_path = base_dir / "rag" / "vector_store" / domain
    
    if not index_path.exists():
        raise FileNotFoundError(f"Vector store index for domain '{domain}' not found at '{index_path}'.")
        
    start_time = time.perf_counter()
    logger.info(f"Loading FAISS index for domain '{domain}' from disk...")
    try:
        embeddings = get_embeddings()
        db = FAISS.load_local(
            str(index_path), 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        duration = time.perf_counter() - start_time
        logger.info(f"FAISS index for domain '{domain}' loaded in {duration:.4f} seconds.")
        return db
    except Exception as e:
        logger.error(f"Failed to load FAISS index for domain '{domain}': {e}")
        raise e

def _retrieve(query: str, domain: str, k: int = 3) -> List[Document]:
    """Helper to fetch documents using the in-memory cached vectorstore."""
    # If the orchestrator has pre-populated ACTIVE_GROUNDING_CONTEXT, return it directly to guarantee grounding layer ownership
    if ACTIVE_GROUNDING_CONTEXT:
        logger.info(f"Returning orchestrator-owned grounding context docs directly for domain '{domain}' (Count: {len(ACTIVE_GROUNDING_CONTEXT)})")
        return ACTIVE_GROUNDING_CONTEXT[:k]

    try:
        db = _load_vectorstore(domain)
        start_time = time.perf_counter()
        docs = db.similarity_search(query, k=k)
        duration = time.perf_counter() - start_time
        logger.info(f"Similarity search in domain '{domain}' returned {len(docs)} documents in {duration:.4f} seconds.")
        return docs
    except FileNotFoundError as e:
        logger.warning(str(e))
        return []
    except Exception as e:
        logger.error(f"Error performing similarity search in domain '{domain}': {e}")
        return []

def retrieve_business(query: str, k: int = 3) -> List[Document]:
    """Retrieves top-k relevant document chunks from the business index (in-memory cached)."""
    return _retrieve(query, "business", k=k)

def retrieve_product(query: str, k: int = 3) -> List[Document]:
    """Retrieves top-k relevant document chunks from the product index (in-memory cached)."""
    return _retrieve(query, "product", k=k)

