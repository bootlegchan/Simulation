"""Unified Test Suite Runner."""
import sys
import unittest
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(base_dir))
    loader = unittest.TestLoader()

    if "--simulation" in sys.argv:
        test_dir = str(base_dir / "tests" / "simulation")
    elif "--all" in sys.argv:
        test_dir = str(base_dir / "tests")
    else:
        test_dir = str(base_dir / "tests" / "unit")

    suite = loader.discover(test_dir, top_level_dir=str(base_dir))
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)

if __name__ == "__main__":
    main()
