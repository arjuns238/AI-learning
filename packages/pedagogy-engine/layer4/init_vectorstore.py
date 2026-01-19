#!/usr/bin/env python3
"""
Initialize the Chroma vector store with Manim dataset embeddings.

Supports multiple datasets:
- ManimBench-v1 (317 examples)
- 3blue1brown-manim (2400+ examples)

Usage:
    python init_vectorstore.py                     # Build with all datasets
    python init_vectorstore.py --rebuild           # Force rebuild existing store
    python init_vectorstore.py --status            # Check store status
    python init_vectorstore.py --datasets manimbench-v1 3blue1brown-manim  # Specific datasets
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from layer4.generator import ManimVectorStore


AVAILABLE_DATASETS = ['manimbench-v1', '3blue1brown-manim']


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Manim vector store with multiple datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Build with all available datasets
    python init_vectorstore.py

    # Rebuild from scratch (useful when adding new datasets)
    python init_vectorstore.py --rebuild

    # Build with specific datasets only
    python init_vectorstore.py --datasets manimbench-v1

    # Check current status
    python init_vectorstore.py --status
        """
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
    parser.add_argument(
        "--datasets",
        nargs='+',
        choices=AVAILABLE_DATASETS,
        default=None,
        help=f"Specific datasets to include (default: all). Options: {', '.join(AVAILABLE_DATASETS)}"
    )

    args = parser.parse_args()

    # Initialize vector store
    print("="*60)
    print("Manim Vector Store Initialization")
    print("="*60)
    print()

    store = ManimVectorStore()

    if not store._initialized:
        print("❌ Vector store initialization failed")
        print("   Make sure chromadb and sentence-transformers are installed:")
        print("   pip install chromadb sentence-transformers")
        sys.exit(1)

    if args.status:
        stats = store.get_stats()
        print(f"\nVector Store Status:")
        print(f"  Location: {stats['storage_path']}")
        print(f"  Collection: {stats['collection_name']}")
        print(f"  Embeddings: {stats['count']}")

        if stats['count'] == 0:
            print("\n  ⚠️  Empty! Run without --status flag to build.")
        else:
            print(f"\n  ✅ Ready for RAG retrieval")
        sys.exit(0)

    # Build or rebuild
    datasets_to_use = args.datasets if args.datasets else AVAILABLE_DATASETS

    print(f"Datasets to index: {', '.join(datasets_to_use)}")
    print()

    store.build(force_rebuild=args.rebuild, datasets=datasets_to_use)

    # Print status
    if store.collection:
        count = store.collection.count()
        print()
        print("="*60)
        print(f"✅ Vector store ready with {count} embeddings")
        print(f"   Location: {store.VECTORSTORE_DIR}")
        print("="*60)
    else:
        print("❌ Vector store build failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
