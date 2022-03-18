#!/usr/bin/env python 3

import unittest
import json
import os

from molpro import OutputFileParser

workdir = os.path.dirname(__file__)


class TestGeneric(unittest.TestCase):
    def test_problem_reporting(self):
        """Test whether we find the correct errors and warnings in a set of generic outputs"""

        decoder = json.JSONDecoder()
        with open(os.path.join(workdir, "files/generic/expected_results.json"), "r") as file:
            resultDefinition = decoder.decode(file.read())

        for currentFile in resultDefinition:
            with open(os.path.join(workdir, "files/generic/" + currentFile), "r") as file:
                parser = OutputFileParser()
                output = parser.parse(file)

                self.assertEqual(resultDefinition[currentFile]["errors"], output.errors,
                                 "Mismatch in discovered errors for file \"%s\"" % currentFile)
                self.assertEqual(resultDefinition[currentFile]["warnings"], output.warnings, "Mismatch in discovered warnings for file \"%s\"" %
                                 currentFile)


    def test_partial_output(self):
        """Ensure that the parsing routine does not error on incomplete output files"""

        basePath = os.path.join(workdir, "files/generic")
        for currentFile in os.listdir(basePath):
            if not currentFile.endswith(".out"):
                continue

            with open(os.path.join(basePath, currentFile)) as file:
                fileContents = file.read()

            lines = fileContents.split("\n")

            for i in range(len(lines), 0, -1):
                contentToTest = "\n".join(lines[ : i ])
                
                parser = OutputFileParser()

                try:
                    parser.parse(contentToTest)
                except Exception as e:
                    self.fail("Parsing of the first %d lines of file \"%s\" raised exception: %s" % (i, currentFile, e))



if __name__ == "__main__":
    unittest.main()
