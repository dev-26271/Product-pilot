import logging
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from rag.embeddings import get_embeddings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

def build_domain_index(domain: str, kb_dir: Path, output_dir: Path) -> None:
    """Loads all PDFs in kb_dir, chunks them, generates embeddings, and saves FAISS index to output_dir."""
    logger.info(f"Starting FAISS index build for domain '{domain}'...")
    
    if not kb_dir.exists():
        logger.warning(f"Knowledge base directory '{kb_dir}' does not exist.")
        return
    
    pdf_files = list(kb_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found inside '{kb_dir}'.")
        return

    documents = []
    for pdf_path in pdf_files:
        logger.info(f"Loading document: {pdf_path}")
        try:
            loader = PyPDFLoader(str(pdf_path))
            documents.extend(loader.load())
        except Exception as e:
            logger.error(f"Failed to load PDF '{pdf_path}': {e}")
            continue

    if not documents:
        logger.warning("No documents loaded successfully.")
        return

    logger.info(f"Loaded {len(documents)} pages. Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.split_documents(documents)
    logger.info(f"Generated {len(chunks)} chunks.")

    logger.info("Generating embeddings and building FAISS index...")
    try:
        embeddings = get_embeddings()
        db = FAISS.from_documents(chunks, embeddings)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        db.save_local(str(output_dir))
        logger.info(f"FAISS index for domain '{domain}' saved successfully to '{output_dir}'.")
    except Exception as e:
        logger.error(f"Failed to generate vectorstore index: {e}")
        raise e

def rebuild_all_indexes() -> None:
    """Triggers FAISS index generation for both business and product directories."""
    base_dir = Path(__file__).resolve().parent.parent
    
    kb_business = base_dir / "knowledge_base" / "business"
    kb_product = base_dir / "knowledge_base" / "product"
    
    store_business = base_dir / "rag" / "vector_store" / "business"
    store_product = base_dir / "rag" / "vector_store" / "product"
    
    build_domain_index("business", kb_business, store_business)
    build_domain_index("product", kb_product, store_product)

if __name__ == "__main__":
    rebuild_all_indexes()
