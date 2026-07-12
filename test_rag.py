import logging
import time
from rag import retrieve_business

# Enable logging output for visibility
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

def main():
    query = "AI healthcare platform for doctors"
    
    print("\n--- RUN 1: Cold start (should trigger initialization and loading) ---")
    start_run1 = time.perf_counter()
    results1 = retrieve_business(query, k=3)
    duration_run1 = time.perf_counter() - start_run1
    print(f"Run 1 completed in {duration_run1:.4f} seconds.")
    
    print("\n--- RUN 2: Cached query (should reuse in-memory objects) ---")
    start_run2 = time.perf_counter()
    results2 = retrieve_business(query, k=3)
    duration_run2 = time.perf_counter() - start_run2
    print(f"Run 2 completed in {duration_run2:.4f} seconds.")

    print(f"\nTime saved by caching: {duration_run1 - duration_run2:.4f} seconds.")

if __name__ == "__main__":
    main()
