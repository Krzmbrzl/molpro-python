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
    runner.run(test_suite)


if __name__ == "__main__":
    main()
