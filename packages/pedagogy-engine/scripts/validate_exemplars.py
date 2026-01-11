"""
Validate exemplars against the PedagogicalIntent schema.

Usage:
    python scripts/validate_exemplars.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from layer1.schema import PedagogicalIntent


def validate_exemplars(exemplar_path: str = "data/exemplars.json"):
    """Validate all exemplars in the JSON file."""

    print("="*60)
    print("Exemplar Validation")
    print("="*60)

    with open(exemplar_path, 'r') as f:
        data = json.load(f)

    exemplars = data.get('exemplars', [])
    print(f"\nFound {len(exemplars)} exemplars to validate\n")

    results = {
        'valid': [],
        'invalid': []
    }

    for i, ex in enumerate(exemplars, 1):
        print(f"\n{i}. Validating: {ex.get('topic', 'Unknown')}")
        print("-" * 60)

        try:
            # Create PedagogicalIntent from exemplar
            intent = PedagogicalIntent(**ex)

            print(f"✓ Schema validation passed")
            print(f"  - Topic: {intent.topic}")
            print(f"  - Domain: {intent.domain}")
            print(f"  - Difficulty: {intent.difficulty_level}/5")
            print(f"  - Core question length: {len(intent.core_question)} chars")
            print(f"  - Mental model length: {len(intent.target_mental_model)} chars")
            print(f"  - Misconception length: {len(intent.common_misconception)} chars")

            results['valid'].append({
                'id': ex.get('id'),
                'topic': intent.topic,
                'intent': intent
            })

        except Exception as e:
            print(f"✗ Validation failed: {e}")
            results['invalid'].append({
                'id': ex.get('id'),
                'topic': ex.get('topic'),
                'error': str(e)
            })

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"✓ Valid: {len(results['valid'])}")
    print(f"✗ Invalid: {len(results['invalid'])}")

    if results['invalid']:
        print("\nFailed exemplars:")
        for item in results['invalid']:
            print(f"  - {item['topic']}: {item['error']}")

    print("\n" + "="*60)
    print("Exemplar Quality Check")
    print("="*60)

    for item in results['valid']:
        intent = item['intent']
        print(f"\n{intent.topic}:")

        # Check question markers
        has_question = intent.core_question.strip().endswith('?')
        print(f"  Core question ends with '?': {'✓' if has_question else '✗'}")

        has_check = intent.check_for_understanding.strip().endswith('?')
        print(f"  Check-for-understanding is a question: {'✓' if has_check else '✗'}")

        # Check length appropriateness
        model_length = len(intent.target_mental_model)
        print(f"  Mental model length: {model_length} ({'✓' if 100 < model_length < 800 else '⚠'} want 100-800)")

        # Check for specificity
        generic_words = ['some', 'often', 'many', 'general', 'typical']
        misconception_lower = intent.common_misconception.lower()
        has_generic = any(word in misconception_lower for word in generic_words)
        print(f"  Misconception specificity: {'⚠ contains generic words' if has_generic else '✓ specific'}")

    return results


if __name__ == "__main__":
    results = validate_exemplars()

    if results['invalid']:
        sys.exit(1)
    else:
        print("\n✓ All exemplars are valid!")
        sys.exit(0)
