import logging
from rag import retrieve_business

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main():
    query = "Agile product management"
    print(f"\n[Test RAG] Running retrieval test for query: '{query}'...")
    
    results = retrieve_business(query, k=3)
    
    if not results:
        print("\n[Test RAG] No results retrieved. Vectorstore index may be empty or not built yet.")
        return

    print(f"\n[Test RAG] Retrieved {len(results)} relevant chunks:")
    for idx, doc in enumerate(results):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "N/A")
        # Format preview text cleanly
        preview = doc.page_content[:250].replace("\n", " ")
        
        print(f"\n--- Match {idx + 1} ---")
        print(f"Source: {source}")
        print(f"Page: {page}")
        print(f"Preview: {preview}...")

if __name__ == "__main__":
    main()
