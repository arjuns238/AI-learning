#!/usr/bin/env python3
"""
Run the complete quick experiment workflow.

This script:
1. Downloads 100 examples from each dataset
2. Runs quick validation (syntax, API checks)
3. Performs dataset analysis
4. Generates summary report

Usage:
    python scripts/run_quick_experiment.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from layer4.validator_quick import validate_dataset_quick

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_quick_experiment():
    """Run the complete quick experiment"""

    logger.info("="*80)
    logger.info("QUICK EXPERIMENT: Manim Dataset Validation")
    logger.info("="*80)

    # Step 1: Download datasets (100 examples each)
    logger.info("\nStep 1: Downloading datasets (100 examples each)...")
    logger.info("-"*80)

    try:
        from scripts.download_manim_datasets import ManimDatasetDownloader, DATASETS

        downloader = ManimDatasetDownloader(
            output_dir=Path("data/manim_datasets"),
            limit=100
        )

        download_results = downloader.download_all()

        successful_downloads = [r for r in download_results if r.get('success')]
        logger.info(f"✅ Downloaded {len(successful_downloads)}/{len(download_results)} datasets successfully")

    except Exception as e:
        logger.error(f"❌ Download failed: {e}", exc_info=True)
        return

    # Step 2: Quick validation
    logger.info("\nStep 2: Running quick validation...")
    logger.info("-"*80)

    validation_results = []
    for result in successful_downloads:
        dataset_name = result['dataset_name']
        dataset_file = Path(result['output_file'])

        logger.info(f"\nValidating {dataset_name}...")

        try:
            output_file = f"data/manim_datasets/metadata/{dataset_name}_quick_validation.json"
            summary = validate_dataset_quick(
                dataset_file=str(dataset_file),
                output_file=output_file
            )
            summary['dataset_name'] = dataset_name
            validation_results.append(summary)

            logger.info(f"  Syntax valid: {summary['syntax_valid']}/{summary['total_examples']} ({summary['syntax_valid_pct']}%)")
            logger.info(f"  Has imports: {summary['has_required_imports']}/{summary['total_examples']} ({summary['has_required_imports_pct']}%)")
            logger.info(f"  Avg quality: {summary['average_quality_score']}")

        except Exception as e:
            logger.error(f"❌ Validation failed for {dataset_name}: {e}")

    # Step 3: Analysis
    logger.info("\nStep 3: Running dataset analysis...")
    logger.info("-"*80)

    try:
        from analysis.analyze_manim_datasets import ManimDatasetAnalyzer

        analyzer = ManimDatasetAnalyzer(data_dir=Path("data/manim_datasets"))

        for result in successful_downloads:
            dataset_name = result['dataset_name']
            logger.info(f"\nAnalyzing {dataset_name}...")

            try:
                statistics = analyzer.analyze_dataset(dataset_name)

                # Generate report
                report_file = Path(f"data/manim_datasets/metadata/{dataset_name}_analysis.md")
                analyzer.generate_report(statistics, output_file=report_file)

                logger.info(f"  ✅ Analysis complete")
                logger.info(f"  Parseable: {statistics.code_patterns.get('parseable', 0)}/{statistics.total_examples}")
                logger.info(f"  Has animations: {statistics.code_patterns.get('has_animations', 0)}/{statistics.total_examples}")

            except Exception as e:
                logger.error(f"❌ Analysis failed for {dataset_name}: {e}")

    except Exception as e:
        logger.error(f"❌ Analysis step failed: {e}", exc_info=True)

    # Step 4: Generate summary report
    logger.info("\nStep 4: Generating summary report...")
    logger.info("-"*80)

    try:
        summary_report = generate_summary_report(validation_results, successful_downloads)

        report_file = Path("data/manim_datasets/metadata/quick_experiment_summary.md")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(summary_report)

        logger.info(f"✅ Summary report saved to {report_file}")

        # Print summary
        print("\n" + "="*80)
        print(summary_report)
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"❌ Failed to generate summary report: {e}", exc_info=True)

    logger.info("\n" + "="*80)
    logger.info("QUICK EXPERIMENT COMPLETE")
    logger.info("="*80)


def generate_summary_report(validation_results: list, download_results: list) -> str:
    """Generate markdown summary report"""

    report = f"""# Quick Experiment Summary Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This quick experiment validates the approach by testing on 100 examples from each dataset.

## Datasets Tested

"""

    for download_result in download_results:
        name = download_result['dataset_name']
        examples = download_result['total_examples']
        report += f"- **{name}**: {examples} examples\n"

    report += "\n## Validation Results\n\n"
    report += "| Dataset | Total | Syntax Valid | Has Imports | Has Scene | Avg Quality |\n"
    report += "|---------|-------|--------------|-------------|-----------|-------------|\n"

    for val_result in validation_results:
        name = val_result['dataset_name']
        total = val_result['total_examples']
        syntax = f"{val_result['syntax_valid']} ({val_result['syntax_valid_pct']}%)"
        imports = f"{val_result['has_required_imports']} ({val_result['has_required_imports_pct']}%)"
        scene = f"{val_result['has_scene_class']} ({val_result['has_scene_class_pct']}%)"
        quality = val_result['average_quality_score']

        report += f"| {name} | {total} | {syntax} | {imports} | {scene} | {quality} |\n"

    report += "\n## Quality Score Distribution\n\n"

    # Aggregate quality distribution
    total_bins = {'0.0-0.3': 0, '0.3-0.5': 0, '0.5-0.7': 0, '0.7-0.9': 0, '0.9-1.0': 0}
    for val_result in validation_results:
        for bin_name, count in val_result['quality_distribution'].items():
            total_bins[bin_name] += count

    total_examples = sum(total_bins.values())

    for bin_name, count in sorted(total_bins.items()):
        pct = count / total_examples * 100 if total_examples > 0 else 0
        bar = '█' * int(pct / 2)  # Visual bar
        report += f"- **{bin_name}**: {count} examples ({pct:.1f}%) {bar}\n"

    report += "\n## Key Findings\n\n"

    # Calculate averages
    avg_syntax = sum(r['syntax_valid_pct'] for r in validation_results) / len(validation_results) if validation_results else 0
    avg_imports = sum(r['has_required_imports_pct'] for r in validation_results) / len(validation_results) if validation_results else 0
    avg_quality = sum(r['average_quality_score'] for r in validation_results) / len(validation_results) if validation_results else 0

    report += f"- **Average Syntax Valid Rate**: {avg_syntax:.1f}%\n"
    report += f"- **Average Has Imports Rate**: {avg_imports:.1f}%\n"
    report += f"- **Average Quality Score**: {avg_quality:.2f}\n"

    # Recommendations
    report += "\n## Recommendations\n\n"

    if avg_syntax < 70:
        report += "- ⚠️ **Low syntax validity** (<70%): Consider more aggressive syntax filtering in full pipeline\n"
    else:
        report += "- ✅ Syntax validity is acceptable\n"

    if avg_imports < 50:
        report += "- ⚠️ **Low import validity** (<50%): Many examples may not be proper Manim code\n"
    else:
        report += "- ✅ Import validity is acceptable\n"

    if avg_quality < 0.5:
        report += "- ⚠️ **Low quality scores** (<0.5): Dataset may need significant curation\n"
    elif avg_quality < 0.7:
        report += "- ⚙️ **Medium quality scores** (0.5-0.7): Expect 50-70% useful examples after full validation\n"
    else:
        report += "- ✅ **High quality scores** (>0.7): Dataset looks promising\n"

    report += "\n## Next Steps\n\n"
    report += "1. Review individual dataset analysis reports\n"
    report += "2. Adjust quality thresholds based on findings\n"
    report += "3. Proceed with full validation pipeline (Phase 2)\n"
    report += "4. Focus on highest-quality datasets for training\n"

    report += "\n---\n*Generated by Quick Experiment Runner*\n"

    return report


if __name__ == "__main__":
    run_quick_experiment()
