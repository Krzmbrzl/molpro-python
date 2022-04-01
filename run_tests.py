#!/usr/bin/env python3
import sys
import os
import unittest

working_dir = os.path.dirname(__file__)

def main():
    # Make sure the "modules" directory from this repo is part of PYTHONPATH (otherwise the imports will fail)
    sys.path.append(os.path.join(working_dir, "modules"))

    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.join(working_dir, "tests"), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return 0 if len(result.errors) == 0 and len(result.failures) == 0 else 1


if __name__ == "__main__":
    main()
