#!/usr/bin/env python 3

import unittest
import os
import tempfile
import filecmp

workdir = os.path.dirname(__file__)
exedir = os.path.join(workdir, "..", "bin")


class TestExecutables(unittest.TestCase):
    def test_create_screening(self):
        """Test whether the create_screening script works as intended"""

        tmp_dir = tempfile.TemporaryDirectory()
        try:
            ret = os.system("python3 " + os.path.join(exedir, "create_screenings.py")
                            + " --screening-file " + os.path.join(workdir, "files", "screening",
                                                                  "details.json")
                            + " --extensions " +
                            os.path.join(workdir, "files",
                                         "screening", "extensions.py")
                            + " --skeleton-file " + os.path.join(workdir,
                                                                 "files", "screening", "skeleton.inp")
                            + " --run-skeleton " +
                            os.path.join(workdir, "files", "screening",
                                         "start_script.sh")
                            + " --aux-file-dir " +
                            os.path.join(workdir, "files",
                                         "screening", "aux-files/")
                            + " --basename base"
                            + " --out-dir " + tmp_dir.name)

            self.assertEqual(ret, 0, "Invocation of create_screening failed")

            expectedDir = os.path.join(
                workdir, "files", "screening", "expected")

            comp = filecmp.dircmp(tmp_dir.name, expectedDir)

            self.assertEqual(
                comp.left_only, [], "Script produced superfluous files")
            self.assertEqual(comp.right_only, [],
                             "Script didn't reproduce all files from expected directory")
            self.assertEqual(comp.diff_files, [],
                             "Script produced different files")
        finally:
            tmp_dir.cleanup()
