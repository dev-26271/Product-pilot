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

# Cache dictionary to avoid recomputing embeddings or re-running retrieval
RETRIEVAL_CACHE: Dict[str, Any] = {}

class RetrievalService:
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
        
        if store_path:
            store_path.parent.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(str(store_path))
            
        return self.vector_store

    def retrieve(self, query: str, k: int = 20) -> List[Dict[str, Any]]:
        """Performs hybrid retrieval (Dense FAISS + Keyword index search) and merges results."""
        cache_key = hashlib.md5(f"retrieve_{query}_{k}".encode("utf-8")).hexdigest()
        if cache_key in RETRIEVAL_CACHE:
            return RETRIEVAL_CACHE[cache_key]
            
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
        
        RETRIEVAL_CACHE[cache_key] = top_results
        return top_results

    def rerank(self, chunks: List[Dict[str, Any]], query: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """Reranks top retrieved chunks using cosine similarity vector distances."""
        cache_key = hashlib.md5(f"rerank_{query}_{len(chunks)}".encode("utf-8")).hexdigest()
        if cache_key in RETRIEVAL_CACHE:
            return RETRIEVAL_CACHE[cache_key]
            
        logger.info(f"Reranking top {len(chunks)} chunks using embeddings model...")
        embeddings = get_embeddings()
        query_vector = embeddings.embed_query(query)
        
        reranked = []
        for r in chunks:
            chunk_vector = embeddings.embed_query(r["content"])
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
        
        RETRIEVAL_CACHE[cache_key] = best_results
        return best_results

    def get_grounding_context(self, query: str) -> List[Dict[str, Any]]:
        """Retrieves and reranks top grounding context."""
        retrieved = self.retrieve(query, k=20)
        if self.use_reranker:
            return self.rerank(retrieved, query, top_n=5)
        return retrieved[:5]
