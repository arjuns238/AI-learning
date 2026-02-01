"""
Test configuration for pedagogy-engine tests.

Ensures that the package modules are importable during testing.
"""

import sys
from pathlib import Path

# Add the pedagogy-engine root to Python path BEFORE any test imports
pedagogy_engine_root = Path(__file__).parent.parent.resolve()
if str(pedagogy_engine_root) not in sys.path:
    sys.path.insert(0, str(pedagogy_engine_root))

# Verify imports work
try:
    import layer1.schema
    import layer3.schema
except ImportError as e:
    print(f"ERROR in conftest: Failed to import modules: {e}")
    print(f"sys.path: {sys.path}")
    raise
