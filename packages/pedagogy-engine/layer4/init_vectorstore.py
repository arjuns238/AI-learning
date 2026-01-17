#!/usr/bin/env python3
"""
Initialize the Chroma vector store with ManimBench-v1 embeddings.

Usage:
    python init_vectorstore.py                 # Build vector store
    python init_vectorstore.py --rebuild       # Force rebuild existing store
    python init_vectorstore.py --status        # Check store status
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from layer4.generator import ManimVectorStore


def main():
    parser = argparse.ArgumentParser(
        description="Initialize ManimBench-v1 vector store"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild the vector store (delete and recreate)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check vector store status"
    )

    args = parser.parse_args()

    # Initialize vector store
    print("Initializing vector store...")
    store = ManimVectorStore()

    if not store._initialized:
        print("❌ Vector store initialization failed")
        sys.exit(1)

    if args.status:
        count = store.collection.count() if store.collection else 0
        print(f"\nVector Store Status:")
        print(f"  Location: {store.VECTORSTORE_DIR}")
        print(f"  Collection: {store.COLLECTION_NAME}")
        print(f"  Embeddings: {count}")
        if count == 0:
            print("\n  Empty! Run without --status flag to build.")
        sys.exit(0)

    # Build or rebuild
    store.build(force_rebuild=args.rebuild)

    # Print status
    if store.collection:
        count = store.collection.count()
        print(f"\n✅ Vector store ready with {count} embeddings")
        print(f"   Location: {store.VECTORSTORE_DIR}")
    else:
        print("❌ Vector store build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
