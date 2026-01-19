#!/usr/bin/env python3
"""
Download Manim datasets from HuggingFace for validation and training.

Usage:
    python scripts/download_manim_datasets.py --limit 100  # Quick experiment
    python scripts/download_manim_datasets.py              # Full download
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from datasets import load_dataset
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Configuration for a HuggingFace Manim dataset"""
    name: str
    hf_id: str
    dataset_type: str  # 'scene_level' or 'step_level'
    priority: int  # 1=high, 2=medium, 3=low
    description: str


# Dataset registry
DATASETS = {
    'smail_bespoke': DatasetConfig(
        name='smail_bespoke',
        hf_id='Smail/bespoke-manim-preprocessed',
        dataset_type='scene_level',
        priority=1,
        description='Bespoke Manim dataset - preprocessed scene-level training data'
    ),
    'suienr_manimbench': DatasetConfig(
        name='suienr_manimbench',
        hf_id='SuienR/ManimBench-v1',
        dataset_type='step_level',
        priority=1,
        description='ManimBench v1 - step-level coding dataset'
    ),
    'thanhkt_manim': DatasetConfig(
        name='thanhkt_manim',
        hf_id='thanhkt/manim_code',
        dataset_type='scene_level',
        priority=2,
        description='Manim code dataset - scene-level examples'
    ),
    'bibby_3b1b': DatasetConfig(
        name='bibby_3b1b',
        hf_id='BibbyResearch/3blue1brown-manim',
        dataset_type='step_level',
        priority=1,
        description='3Blue1Brown Manim - high-quality step-level dataset'
    )
}


class ManimDatasetDownloader:
    """Download and organize Manim datasets from HuggingFace"""

    def __init__(self, output_dir: Path, limit: Optional[int] = None):
        """
        Initialize downloader.

        Args:
            output_dir: Base directory for downloaded datasets
            limit: If set, only download first N examples per dataset (for quick experiments)
        """
        self.output_dir = Path(output_dir)
        self.limit = limit
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectory for each dataset
        self.raw_dir = self.output_dir / "raw"
        self.raw_dir.mkdir(exist_ok=True)

    def download_dataset(self, config: DatasetConfig) -> Dict:
        """
        Download a single dataset from HuggingFace.

        Args:
            config: Dataset configuration

        Returns:
            Metadata dictionary with download statistics
        """
        logger.info(f"Downloading {config.name} from {config.hf_id}")

        # Create dataset directory
        dataset_dir = self.raw_dir / config.name
        dataset_dir.mkdir(exist_ok=True)

        try:
            # Load dataset from HuggingFace
            logger.info(f"Loading dataset {config.hf_id}...")

            # Try to load with streaming first to check availability
            dataset = load_dataset(config.hf_id, split='train', streaming=True)

            # Collect examples
            examples = []
            for idx, example in enumerate(dataset):
                if self.limit and idx >= self.limit:
                    break
                examples.append(example)

                if (idx + 1) % 10 == 0:
                    logger.info(f"Downloaded {idx + 1} examples...")

            logger.info(f"Successfully downloaded {len(examples)} examples from {config.name}")

            # Save examples as JSONL (one JSON object per line)
            output_file = dataset_dir / f"{config.name}_raw.jsonl"
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in examples:
                    f.write(json.dumps(example) + '\n')

            logger.info(f"Saved to {output_file}")

            # Generate metadata
            metadata = {
                'dataset_name': config.name,
                'hf_id': config.hf_id,
                'dataset_type': config.dataset_type,
                'priority': config.priority,
                'description': config.description,
                'download_timestamp': datetime.now().isoformat(),
                'total_examples': len(examples),
                'limit_applied': self.limit,
                'output_file': str(output_file),
                'success': True,
                'error': None
            }

            # Save metadata
            metadata_file = dataset_dir / f"{config.name}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            return metadata

        except Exception as e:
            logger.error(f"Failed to download {config.name}: {e}")

            metadata = {
                'dataset_name': config.name,
                'hf_id': config.hf_id,
                'download_timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }

            return metadata

    def download_all(self, datasets: Optional[List[str]] = None) -> List[Dict]:
        """
        Download all datasets or a subset.

        Args:
            datasets: List of dataset names to download (None = all)

        Returns:
            List of metadata dictionaries
        """
        if datasets is None:
            datasets = list(DATASETS.keys())

        logger.info(f"Starting download of {len(datasets)} datasets")
        if self.limit:
            logger.info(f"Limit: {self.limit} examples per dataset (quick experiment mode)")

        results = []
        for dataset_name in datasets:
            if dataset_name not in DATASETS:
                logger.warning(f"Unknown dataset: {dataset_name}, skipping")
                continue

            config = DATASETS[dataset_name]
            metadata = self.download_dataset(config)
            results.append(metadata)

        # Save overall summary
        summary_file = self.output_dir / "download_summary.json"
        summary = {
            'download_session': datetime.now().isoformat(),
            'limit_applied': self.limit,
            'total_datasets': len(results),
            'successful_downloads': sum(1 for r in results if r.get('success')),
            'failed_downloads': sum(1 for r in results if not r.get('success')),
            'datasets': results
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\n=== Download Summary ===")
        logger.info(f"Total datasets: {summary['total_datasets']}")
        logger.info(f"Successful: {summary['successful_downloads']}")
        logger.info(f"Failed: {summary['failed_downloads']}")
        logger.info(f"Summary saved to: {summary_file}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description='Download Manim datasets from HuggingFace',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick experiment (100 examples per dataset)
  python scripts/download_manim_datasets.py --limit 100

  # Download specific datasets
  python scripts/download_manim_datasets.py --datasets smail_bespoke suienr_manimbench

  # Full download (all datasets, no limit)
  python scripts/download_manim_datasets.py

  # Custom output directory
  python scripts/download_manim_datasets.py --output /path/to/data
        """
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/manim_datasets',
        help='Output directory for downloaded datasets (default: data/manim_datasets)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of examples per dataset (for quick experiments)'
    )

    parser.add_argument(
        '--datasets',
        nargs='+',
        choices=list(DATASETS.keys()),
        default=None,
        help='Specific datasets to download (default: all)'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available datasets and exit'
    )

    args = parser.parse_args()

    # List datasets if requested
    if args.list:
        print("\nAvailable datasets:")
        print("-" * 80)
        for name, config in DATASETS.items():
            print(f"\n{name}:")
            print(f"  HuggingFace ID: {config.hf_id}")
            print(f"  Type: {config.dataset_type}")
            print(f"  Priority: {config.priority}")
            print(f"  Description: {config.description}")
        print("\n")
        return

    # Run downloader
    downloader = ManimDatasetDownloader(
        output_dir=Path(args.output),
        limit=args.limit
    )

    results = downloader.download_all(datasets=args.datasets)

    # Print results
    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE")
    print("="*80)
    for result in results:
        status = "✅ SUCCESS" if result.get('success') else "❌ FAILED"
        examples = result.get('total_examples', 0)
        print(f"{status} | {result['dataset_name']}: {examples} examples")
        if not result.get('success'):
            print(f"  Error: {result.get('error')}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
