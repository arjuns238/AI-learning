#!/usr/bin/env python3
"""
Quick test of the RAG retrieval system.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from layer4.generator import ManimVectorStore

def main():
    print("Testing ManimBench RAG Retrieval\n" + "="*60)

    # Initialize vector store
    print("\n1. Initializing vector store...")
    store = ManimVectorStore()

    if not store._initialized:
        print("❌ Vector store not initialized")
        return

    count = store.collection.count()
    print(f"✓ Vector store loaded with {count} embeddings")

    # Test queries
    test_queries = [
        "Create a circle that moves from left to right",
        "Animate gradient descent optimization",
        "Show a mathematical equation",
        "Draw a graph with axes"
    ]

    print("\n2. Testing retrieval with sample queries:\n")

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        print("-" * 60)

        results = store.retrieve(query, top_k=3)

        if results:
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i} (Similarity: {result['similarity']:.3f})")
                print(f"  Type: {result['type']}")
                print(f"  Description: {result['description'][:100]}...")
                print(f"  Code preview: {result['code'][:150]}...")
        else:
            print("  No results found")

    print("\n" + "="*60)
    print("✓ RAG retrieval test complete!")

if __name__ == "__main__":
    main()
