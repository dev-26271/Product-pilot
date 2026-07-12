import logging
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)

def _retrieve(query: str, domain: str, k: int = 3) -> List[Document]:
    """Helper to load FAISS index from disk and run similarity search."""
    base_dir = Path(__file__).resolve().parent.parent
    index_path = base_dir / "rag" / "vector_store" / domain
    
    if not index_path.exists():
        logger.warning(f"Vector store index for domain '{domain}' not found at '{index_path}'.")
        return []
        
    try:
        embeddings = get_embeddings()
        db = FAISS.load_local(
            str(index_path), 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        docs = db.similarity_search(query, k=k)
        return docs
    except Exception as e:
        logger.error(f"Error performing similarity search in domain '{domain}': {e}")
        return []

def retrieve_business(query: str, k: int = 3) -> List[Document]:
    """Retrieves top-k relevant document chunks from the business index."""
    return _retrieve(query, "business", k=k)

def retrieve_product(query: str, k: int = 3) -> List[Document]:
    """Retrieves top-k relevant document chunks from the product index."""
    return _retrieve(query, "product", k=k)
