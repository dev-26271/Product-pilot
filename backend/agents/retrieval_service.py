import os
import json
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)

def sanitize_project_id(project_id: str) -> str:
    import re
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_\-]', '_', project_id)
    return sanitized

# Cache dictionary to avoid recomputing embeddings or re-running retrieval
RETRIEVAL_CACHE: Dict[str, Any] = {}

class RetrievalService:
    _cached_global_store = None
    _cached_global_documents = None
    
    _cached_project_stores = {}
    _cached_project_documents = {}

    @classmethod
    def clear_cache(cls, project_id=None):
        if project_id:
            sanitized = sanitize_project_id(project_id)
            cls._cached_project_stores.pop(sanitized, None)
            cls._cached_project_documents.pop(sanitized, None)
        else:
            cls._cached_global_store = None
            cls._cached_global_documents = None
            cls._cached_project_stores.clear()
            cls._cached_project_documents.clear()

    def __init__(self, use_reranker: bool = True):
        self.use_reranker = use_reranker
        self.documents: List[Dict[str, Any]] = []
        self.vector_store: Any = None

    def ingest_documents(self, kb_dir: Path) -> List[Dict[str, Any]]:
        """Loads and chunks all documents from the given directory (PDF, MD, TXT, DOCX, JSON, CSV)."""
        logger.info(f"Ingesting documents from {kb_dir}...")
        ingested = []
        if not kb_dir.exists():
            logger.warning(f"KB directory does not exist: {kb_dir}")
            return ingested

        for file_path in kb_dir.rglob("*"):
            if file_path.is_dir():
                continue
            ext = file_path.suffix.lower()
            if ext not in [".pdf", ".md", ".txt", ".docx", ".json", ".csv"]:
                continue

            try:
                content = ""
                pages = []
                
                if ext == ".pdf":
                    from langchain_community.document_loaders import PyPDFLoader
                    loader = PyPDFLoader(str(file_path))
                    pdf_pages = loader.load()
                    for idx, page in enumerate(pdf_pages):
                        pages.append((idx + 1, page.page_content))
                elif ext == ".docx":
                    content = self._read_docx(file_path)
                    pages = [(1, content)]
                elif ext in [".txt", ".md"]:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    pages = [(1, content)]
                elif ext == ".csv":
                    import csv
                    rows = []
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.reader(f)
                        for r in reader:
                            rows.append(", ".join(r))
                    content = "\n".join(rows)
                    pages = [(1, content)]
                elif ext == ".json":
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                    content = json.dumps(data, indent=2)
                    pages = [(1, content)]

                # Intelligent chunking for each page/content
                for page_num, text in pages:
                    chunks = self._intelligent_chunk(text)
                    for chunk_idx, chunk in enumerate(chunks):
                        chunk_id = f"{file_path.name}_p{page_num}_c{chunk_idx}"
                        metadata = {
                            "source": file_path.name,
                            "document_type": ext[1:],
                            "page": page_num,
                            "chunk_id": chunk_id,
                            "tags": [file_path.parent.name, ext[1:]],
                            "timestamp": datetime.now().isoformat()
                        }
                        ingested.append({
                            "content": chunk,
                            "metadata": metadata
                        })
            except Exception as e:
                logger.error(f"Error ingesting file {file_path.name}: {e}")
                
        self.documents.extend(ingested)
        return ingested

    def _read_docx(self, path: Path) -> str:
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(path) as docx:
                xml_content = docx.read('word/document.xml')
                root = ET.fromstring(xml_content)
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                paragraphs = []
                for p in root.findall('.//w:p', ns):
                    texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error(f"Error reading DOCX: {e}")
            return ""

    def _intelligent_chunk(self, text: str) -> List[str]:
        """Intelligent chunking splitting by headings, sections, paragraphs keeping boundaries intact."""
        if not text.strip():
            return []
            
        import re
        sections = re.split(r'(\n#+\s+|\n\n)', text)
        chunks = []
        current_chunk = ""
        
        for part in sections:
            if len(current_chunk) + len(part) > 800:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = part
            else:
                current_chunk += part
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks

    def load_vector_store_if_needed(self, base_dir: Path, project_id: str = None) -> float:
        """Loads and merges global indexes with project-specific FAISS stores dynamically."""
        t_start = time.perf_counter()
        
        # Load business & product fresh from disk to avoid in-memory pollution
        embeddings = get_embeddings()
        try:
            store_b = FAISS.load_local(str(base_dir / "rag" / "vector_store" / "business"), embeddings, allow_dangerous_deserialization=True)
            store_p = FAISS.load_local(str(base_dir / "rag" / "vector_store" / "product"), embeddings, allow_dangerous_deserialization=True)
            store_b.merge_from(store_p)
        except Exception as e:
            logger.warning(f"Failed to load global indexes: {e}. Building mock store...")
            # Fallback to a mock FAISS index if directories are missing
            from langchain_core.documents import Document
            store_b = FAISS.from_documents([Document(page_content="Global Business Grounding", metadata={"source": "mock"})], embeddings)
            
        # Ingest and merge project-specific uploads FAISS index if project_id is provided
        if project_id:
            sanitized_id = sanitize_project_id(project_id)
            project_dir = base_dir / "knowledge_base" / "projects" / sanitized_id
            project_store_path = project_dir / "vector_store"
            
            if project_store_path.exists():
                try:
                    store_u = FAISS.load_local(str(project_store_path), embeddings, allow_dangerous_deserialization=True)
                    store_b.merge_from(store_u)
                except Exception as e:
                    logger.error(f"Failed to load project-specific vector store: {e}")
            else:
                # Fallback build from raw uploads folder if folder exists but no serialized index
                project_uploads_dir = project_dir / "uploads"
                if project_uploads_dir.exists() and list(project_uploads_dir.glob("*")):
                    try:
                        temp_service = RetrievalService()
                        temp_service.ingest_documents(project_uploads_dir)
                        if temp_service.documents:
                            new_store = temp_service.build_vector_store()
                            if new_store:
                                project_store_path.parent.mkdir(parents=True, exist_ok=True)
                                new_store.save_local(str(project_store_path))
                                store_b.merge_from(new_store)
                    except Exception as e:
                        logger.error(f"Failed to dynamically compile project vector store: {e}")
                        
        self.vector_store = store_b
        return time.perf_counter() - t_start

    def build_vector_store(self, store_path: Path = None):
        """Builds in-memory FAISS store from ingested documents."""
        if not self.documents:
            logger.warning("No ingested documents to build vector store.")
            return None
            
        logger.info("Generating embeddings and building vector store index...")
        start_time = time.perf_counter()
        
        lc_docs = [
            Document(page_content=doc["content"], metadata=doc["metadata"])
            for doc in self.documents
        ]
        
        embeddings = get_embeddings()
        self.vector_store = FAISS.from_documents(lc_docs, embeddings)
        
        duration = time.perf_counter() - start_time
        logger.info(f"Vector store built in {duration:.4f} seconds.")
        
        # Also cache the newly built vector store
        RetrievalService._cached_vector_store = self.vector_store
        RetrievalService._cached_documents = self.documents
        
        if store_path:
            store_path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(str(store_path))
            
        return self.vector_store

    def retrieve(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        """Performs hybrid retrieval (Dense FAISS + Keyword index search) and merges results."""
        logger.info(f"Retrieving grounded context for query: '{query[:50]}'")
        results = []
        
        # 1. Dense Embedding Retrieval
        dense_results = []
        if self.vector_store:
            docs = self.vector_store.similarity_search_with_score(query, k=k)
            for doc, score in docs:
                confidence = float(max(0.0, min(1.0, 1.0 - (score / 2.0))))
                dense_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "confidence": confidence,
                    "source_type": "dense"
                })
                
        # 2. Keyword Search Heuristic
        keyword_results = []
        keywords = [w.lower() for w in query.split() if len(w) > 3]
        for doc in self.documents:
            match_count = 0
            doc_lower = doc["content"].lower()
            for kw in keywords:
                if kw in doc_lower:
                    match_count += 1
            if match_count > 0:
                confidence = float(min(1.0, match_count / max(1, len(keywords))))
                keyword_results.append({
                    "content": doc["content"],
                    "metadata": doc["metadata"],
                    "confidence": confidence * 0.8,
                    "source_type": "keyword"
                })
                
        # 3. Merge and De-duplicate
        merged = {}
        for r in dense_results + keyword_results:
            cid = r["metadata"].get("chunk_id") or f"{r['metadata'].get('source', 'unknown')}_p{r['metadata'].get('page', 1)}_hash_{hash(r['content'])}"
            if cid not in merged or r["confidence"] > merged[cid]["confidence"]:
                merged[cid] = r
                
        sorted_results = sorted(merged.values(), key=lambda x: x["confidence"], reverse=True)
        top_results = sorted_results[:k]
        
        return top_results

    def rerank(self, chunks: List[Dict[str, Any]], query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Reranks top retrieved chunks using cosine similarity vector distances."""
        logger.info(f"Reranking top {len(chunks)} chunks using embeddings model...")
        embeddings = get_embeddings()
        query_vector = embeddings.embed_query(query)
        
        # Batched embeddings call to avoid sequential processing loop
        texts = [r["content"] for r in chunks]
        chunk_vectors = embeddings.embed_documents(texts)
        
        reranked = []
        for r, chunk_vector in zip(chunks, chunk_vectors):
            import math
            dot = sum(a * b for a, b in zip(query_vector, chunk_vector))
            norm_q = math.sqrt(sum(a * a for a in query_vector))
            norm_c = math.sqrt(sum(a * a for a in chunk_vector))
            cosine_score = float(dot / (norm_q * norm_c)) if norm_q and norm_c else 0.0
            
            final_confidence = float(cosine_score * 0.7 + r["confidence"] * 0.3)
            r["confidence"] = final_confidence
            reranked.append(r)
            
        reranked_sorted = sorted(reranked, key=lambda x: x["confidence"], reverse=True)
        best_results = reranked_sorted[:top_n]
        
        return best_results

    def get_grounding_context(self, query: str, project_id: str = None) -> List[Dict[str, Any]]:
        """Retrieves and reranks top grounding context with step-by-step profiling."""
        from backend.profiler import PerformanceProfiler
        profiler = PerformanceProfiler.get_instance()
        
        # Record overall sub-timing for RAG Loading & Search
        profiler.start_sub("RAG Loading & Search")
        
        # 1. Model Load
        t_model_start = time.perf_counter()
        embeddings = get_embeddings()
        model_load_time = time.perf_counter() - t_model_start
        
        # 2. FAISS Load
        base_dir = Path(__file__).resolve().parent.parent.parent
        faiss_load_time = self.load_vector_store_if_needed(base_dir, project_id=project_id)
        
        # 3. Similarity Search
        t_search_start = time.perf_counter()
        retrieved = self.retrieve(query, k=20)
        search_time = time.perf_counter() - t_search_start
        
        # 4. Reranking
        t_rerank_start = time.perf_counter()
        if self.use_reranker and retrieved:
            reranked = self.rerank(retrieved, query, top_n=5)
        else:
            reranked = retrieved[:5]
        rerank_time = time.perf_counter() - t_rerank_start
        
        # 5. Context Assembly
        t_assembly_start = time.perf_counter()
        final_context = reranked
        assembly_time = time.perf_counter() - t_assembly_start
        
        profiler.end_sub("RAG Loading & Search")
        
        total_rag_time = model_load_time + faiss_load_time + search_time + rerank_time + assembly_time
        
        # Record timings inside PerformanceProfiler sub-timings
        profiler.sub_timings["RAG Model Load"] = model_load_time
        profiler.sub_timings["RAG FAISS Load"] = faiss_load_time
        profiler.sub_timings["RAG Similarity Search"] = search_time
        profiler.sub_timings["RAG Reranking"] = rerank_time
        profiler.sub_timings["RAG Context Assembly"] = assembly_time
        
        def format_ms(seconds: float) -> str:
            ms = seconds * 1000.0
            if ms == 0:
                return "0 ms"
            elif ms < 0.1:
                return f"{ms:.3f} ms"
            elif ms < 1.0:
                return f"{ms:.2f} ms"
            elif ms < 10.0:
                return f"{ms:.1f} ms"
            else:
                return f"{ms:.0f} ms"
        
        # Print RAG Performance Timing Report to logs & stdout
        report = f"""
RAG Performance
---------------
Model Load ............ {format_ms(model_load_time)}
FAISS Load ............ {format_ms(faiss_load_time)}
Similarity Search ..... {format_ms(search_time)}
Reranking ............. {format_ms(rerank_time)}
Context Assembly ...... {format_ms(assembly_time)}

Total ................. {format_ms(total_rag_time)}
"""
        logger.info(report)
        print(report)
        
        return final_context
