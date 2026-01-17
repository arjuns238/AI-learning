#!/usr/bin/env python3
"""
Quick Experiment: Pandas-based dataset validation

Loads datasets directly into pandas DataFrames and performs validation.
Much simpler than file-based approach!

Usage:
    python scripts/quick_experiment_pandas.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from datasets import load_dataset
from layer4.validator_quick import QuickValidator
import logging
from datetime import datetime
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dataset configurations
DATASETS = {
    'smail_bespoke': {
        'hf_id': 'Smail/bespoke-manim-preprocessed',
        'type': 'scene_level',
        'priority': 1
    },
    'suienr_manimbench': {
        'hf_id': 'SuienR/ManimBench-v1',
        'type': 'step_level',
        'priority': 1
    },
    'thanhkt_manim': {
        'hf_id': 'thanhkt/manim_code',
        'type': 'scene_level',
        'priority': 2
    },
    'bibby_3b1b': {
        'hf_id': 'BibbyResearch/3blue1brown-manim',
        'type': 'step_level',
        'priority': 1
    }
}


def load_dataset_to_pandas(hf_id: str, limit: int = 100) -> pd.DataFrame:
    """Load HuggingFace dataset directly into pandas DataFrame"""
    logger.info(f"Loading {hf_id} (limit: {limit})...")

    try:
        # Load with streaming to limit examples
        dataset = load_dataset(hf_id, split='train', streaming=True)

        # Take first N examples
        examples = list(dataset.take(limit))

        # Convert to DataFrame
        df = pd.DataFrame(examples)

        logger.info(f"✅ Loaded {len(df)} examples")
        logger.info(f"Columns: {list(df.columns)}")

        return df

    except Exception as e:
        logger.error(f"❌ Failed to load {hf_id}: {e}")
        return pd.DataFrame()


def validate_dataframe(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """Validate all examples in a DataFrame"""
    logger.info(f"\nValidating {dataset_name}...")

    if df.empty:
        return df

    # Find the code column (might be 'code', 'text', 'solution', etc.)
    code_col = None
    for col in ['code', 'text', 'solution', 'answer']:
        if col in df.columns:
            code_col = col
            break

    if not code_col:
        logger.error(f"No code column found in {dataset_name}. Columns: {list(df.columns)}")
        return df

    logger.info(f"Using code column: '{code_col}'")

    # Initialize validator
    validator = QuickValidator()

    # Validate each row
    validations = []
    for idx, row in df.iterrows():
        code = row[code_col]
        if pd.isna(code) or not code:
            continue

        result = validator.validate(str(code))
        validations.append({
            'is_valid_python': result.is_valid_python,
            'has_required_imports': result.has_required_imports,
            'scene_classes': ','.join(result.scene_classes),
            'api_issues': ','.join(result.api_issues),
            'quality_score': result.quality_score,
            'error_message': result.error_message
        })

    # Add validation results as new columns
    validation_df = pd.DataFrame(validations)
    df_validated = pd.concat([df.reset_index(drop=True), validation_df], axis=1)

    logger.info(f"✅ Validated {len(validations)} examples")

    return df_validated


def analyze_dataframe(df: pd.DataFrame, dataset_name: str) -> dict:
    """Generate statistics from validated DataFrame"""
    if df.empty or 'quality_score' not in df.columns:
        return {}

    stats = {
        'dataset_name': dataset_name,
        'total_examples': len(df),
        'syntax_valid': df['is_valid_python'].sum() if 'is_valid_python' in df.columns else 0,
        'has_imports': df['has_required_imports'].sum() if 'has_required_imports' in df.columns else 0,
        'has_scene_class': (df['scene_classes'].str.len() > 0).sum() if 'scene_classes' in df.columns else 0,
        'no_api_issues': (df['api_issues'].str.len() == 0).sum() if 'api_issues' in df.columns else 0,
        'avg_quality': df['quality_score'].mean() if 'quality_score' in df.columns else 0,
        'quality_bins': {}
    }

    # Quality distribution
    if 'quality_score' in df.columns:
        bins = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
        labels = ['0.0-0.3', '0.3-0.5', '0.5-0.7', '0.7-0.9', '0.9-1.0']
        df['quality_bin'] = pd.cut(df['quality_score'], bins=bins, labels=labels, include_lowest=True)
        stats['quality_bins'] = df['quality_bin'].value_counts().to_dict()

    return stats


def generate_report(all_stats: list) -> str:
    """Generate markdown summary report"""
    report = f"""# Quick Experiment Results (Pandas-based)

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

Tested 4 HuggingFace datasets with 100 examples each (400 total).

## Results by Dataset

"""

    # Table
    report += "| Dataset | Total | Syntax Valid | Has Imports | Has Scene | Avg Quality |\n"
    report += "|---------|-------|--------------|-------------|-----------|-------------|\n"

    for stats in all_stats:
        if not stats:
            continue

        name = stats['dataset_name']
        total = stats['total_examples']
        syntax = stats.get('syntax_valid', 0)
        syntax_pct = (syntax / total * 100) if total > 0 else 0
        imports = stats.get('has_imports', 0)
        imports_pct = (imports / total * 100) if total > 0 else 0
        scene = stats.get('has_scene_class', 0)
        scene_pct = (scene / total * 100) if total > 0 else 0
        quality = stats.get('avg_quality', 0)

        report += f"| {name} | {total} | {syntax} ({syntax_pct:.1f}%) | "
        report += f"{imports} ({imports_pct:.1f}%) | {scene} ({scene_pct:.1f}%) | {quality:.2f} |\n"

    report += "\n## Quality Score Distribution (All Datasets)\n\n"

    # Aggregate quality bins
    total_bins = Counter()
    for stats in all_stats:
        if stats and 'quality_bins' in stats:
            for bin_name, count in stats['quality_bins'].items():
                total_bins[str(bin_name)] += count

    total_examples = sum(total_bins.values())
    for bin_name in ['0.0-0.3', '0.3-0.5', '0.5-0.7', '0.7-0.9', '0.9-1.0']:
        count = total_bins.get(bin_name, 0)
        pct = (count / total_examples * 100) if total_examples > 0 else 0
        bar = '█' * int(pct / 2)
        report += f"- **{bin_name}**: {count} examples ({pct:.1f}%) {bar}\n"

    report += "\n## Key Findings\n\n"

    # Calculate averages
    if all_stats:
        avg_syntax = sum(s.get('syntax_valid', 0) / s['total_examples'] * 100
                        for s in all_stats if s) / len([s for s in all_stats if s])
        avg_quality = sum(s.get('avg_quality', 0) for s in all_stats if s) / len([s for s in all_stats if s])

        report += f"- **Average Syntax Valid Rate**: {avg_syntax:.1f}%\n"
        report += f"- **Average Quality Score**: {avg_quality:.2f}\n\n"

        if avg_syntax >= 70:
            report += "✅ Good syntax validity\n"
        else:
            report += "⚠️ Low syntax validity - may need more filtering\n"

        if avg_quality >= 0.7:
            report += "✅ High quality dataset - ready for training\n"
        elif avg_quality >= 0.5:
            report += "⚙️ Medium quality - expect 50-70% usable after full validation\n"
        else:
            report += "⚠️ Low quality - may need alternative sources\n"

    report += "\n---\n*Generated with pandas-based quick experiment*\n"

    return report


def main():
    """Run the complete quick experiment"""

    print("="*80)
    print("QUICK EXPERIMENT: Manim Dataset Validation (Pandas)")
    print("="*80)

    all_dataframes = {}
    all_stats = []

    # Process each dataset
    for dataset_name, config in DATASETS.items():
        print(f"\n{'='*80}")
        print(f"Processing: {dataset_name}")
        print(f"{'='*80}")

        # Load to pandas
        df = load_dataset_to_pandas(config['hf_id'], limit=100)

        if df.empty:
            logger.warning(f"Skipping {dataset_name} - empty dataset")
            continue

        # Validate
        df_validated = validate_dataframe(df, dataset_name)

        # Analyze
        stats = analyze_dataframe(df_validated, dataset_name)

        # Store
        all_dataframes[dataset_name] = df_validated
        all_stats.append(stats)

        # Print quick stats
        if stats:
            print(f"\n📊 {dataset_name} Statistics:")
            print(f"  Syntax valid: {stats['syntax_valid']}/{stats['total_examples']} ({stats['syntax_valid']/stats['total_examples']*100:.1f}%)")
            print(f"  Average quality: {stats['avg_quality']:.2f}")

    # Generate summary report
    print("\n" + "="*80)
    print("GENERATING SUMMARY REPORT")
    print("="*80)

    report = generate_report(all_stats)

    # Save report
    output_dir = Path("data/manim_datasets/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "quick_experiment_pandas_summary.md"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n✅ Report saved to: {report_file}")

    # Print report
    print("\n" + "="*80)
    print(report)
    print("="*80)

    # Optionally save DataFrames as CSV
    print("\n💾 Saving validated DataFrames as CSV...")
    for name, df in all_dataframes.items():
        csv_file = output_dir / f"{name}_validated.csv"
        df.to_csv(csv_file, index=False)
        print(f"  ✅ {csv_file}")

    print("\n" + "="*80)
    print("EXPERIMENT COMPLETE!")
    print("="*80)
    print(f"\nResults saved to: {output_dir}/")
    print("- Summary: quick_experiment_pandas_summary.md")
    print("- Validated CSVs: *_validated.csv")


if __name__ == "__main__":
    main()
