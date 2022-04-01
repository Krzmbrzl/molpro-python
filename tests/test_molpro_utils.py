#!/usr/bin/env python3

import unittest

from molpro import IterationTable
from molpro import utils


class TestIterationTable(unittest.TestCase):
    def test_interface(self):
        """Test whether the general interface of the IterationTable class is working as intended"""
        headers = ["A", "B", "C"]
        data = [
            ["One", 1, 0.1],
            ["Two", 2, 0.2],
            ["Three", 3, 0.3]
        ]

        table = IterationTable(columnHeaders=headers, iterations=data)

        self.assertEqual(table.iteration(1), data[0])
        self.assertEqual(table.iteration(3), data[2])

        self.assertEqual(table.column(0), ["One", "Two", "Three"])
        self.assertEqual(table.column(2), [0.1, 0.2, 0.3])

    def test_named_column_lookup(self):
        """Test whether the different columns can be accessed by name"""
        headers = ["A", "B", "C"]
        data = [
            ["One", 1, 0.1],
            ["Two", 2, 0.2],
            ["Three", 3, 0.3]
        ]

        table = IterationTable(columnHeaders=headers, iterations=data)

        self.assertEqual(table.column("A"), ["One", "Two", "Three"])
        self.assertEqual(table.column("B"), [1, 2, 3])

        with self.assertRaises(KeyError):
            table.column("Doesn't exist")


class TestMolproUtils(unittest.TestCase):
    def test_process_columns(self):
        line = "A B C D"
        expectedResult = ["A", "B", "C", "D"]

        result = utils.process_columns(line)

        self.assertEqual(result, expectedResult)

        line = "A,B,C,,D"
        expectedResult = ["A", "B", "C", "", "D"]
        result = utils.process_columns(line, delimiter=",")
        self.assertEqual(result, expectedResult)
        result = utils.process_columns(line, delimiter=",", remove_empty=True)
        expectedResult = ["A", "B", "C", "D"]
        self.assertEqual(result, expectedResult)

        line = "1 0.5 bla 1D-5 0.1E+7"
        expectedResult = [1, 0.5, "bla", 1E-5, 0.1E7]
        result = utils.process_columns(
            line, types=[[int, float, str, float, float]])
        self.assertEqual(result, expectedResult)

        # Use optional columns
        line = "A 2 C"
        expectedResult = ["A", 2, "C"]
        result = utils.process_columns(
            line, types=[[int, str, int, str], [str, int, str]])
        self.assertEqual(result, expectedResult)

        # Use composite types
        line = "A 2 B C"
        expectedResult = ["A", (2, "B"), "C"]
        result = utils.process_columns(
            line, types=[[str, (int, str), str]])
        self.assertEqual(result, expectedResult)

    def test_parse_iteration_table(self):
        lines = [
            "ITER           ETOT              DE          GRAD        DDIFF     DIIS  NEXP   TIME (IT)  TIME(TOT)  DIAG",
            "1      -75.98578855     -75.98578855     0.00D+00     0.40D+00     0     0       0.01      0.07    start",
            "2      -76.01569782      -0.02990927     0.37D-01     0.77D-01     1     0       0.00      0.07    diag",
            "3      -76.02461371      -0.00891589     0.20D-01     0.26D-01     2     0       0.01      0.08    diag",
        ]
        lineIt = iter(range(len(lines)))

        parsedTable = utils.parse_iteration_table(lines, lineIt, col_types=[[int, float, float, float, float, int, int, float, float, str]],
                                                  del_cols={"ITER"}, substitutions={"TIME (IT)": "TIME(IT)"})
        expectedTable = IterationTable(columnHeaders=[
                                       "ETOT", "DE", "GRAD", "DDIFF", "DIIS", "NEXP", "TIME(IT)", "TIME(TOT)", "DIAG"],
                                       iterations=[
                                           [-75.98578855, -75.98578855, 0,
                                               0.4, 0, 0, 0.01, 0.07, "start"],
                                           [-76.01569782, -0.02990927, 0.37E-1,
                                               0.77E-1, 1, 0, 0, 0.07, "diag"],
                                           [-76.02461371, -0.00891589, 0.2E-1,
                                               0.26E-1, 2, 0, 0.01, 0.08, "diag"]
        ])

        self.assertEqual(parsedTable, expectedTable)


        lines = [
            "ITER  NCI SQNORM     DIAG(H_EFF)      E(PROJ)+DL      DL        |RES|     NSV   SV INCL   SV EXCL   DIIS     TIME   TIME/IT",
            " 1    1  1.2838   -230.42152688   -230.20919500  -7.11e-01   2.07e+00     13  3.58e-01  1.39e-15   1  1   6354.45  6354.45",
            " 2    1  1.3172   -230.44447074   -230.47744042  -5.54e-02   3.20e-01     13  2.58e-01  2.22e-15         12693.51  6346.76",
        ]
        lineIt = iter(range(len(lines)))

        parsedTable = utils.parse_iteration_table(lines, lineIt, col_types=[
            [int, int, float, float, float, float, float, int, float, float, (int, int), float, float],
            [int, int, float, float, float, float, float, int, float, float, None, float, float]
            ], del_cols={"ITER"}, substitutions={"SV INCL": "SV_INCL", "SV EXCL": "SV_EXCL"})
        expectedTable = IterationTable(columnHeaders=["NCI", "SQNORM", "DIAG(H_EFF)", "E(PROJ)+DL", "DL", "|RES|", "NSV", "SV_INCL", "SV_EXCL",
            "DIIS", "TIME", "TIME/IT"],
            iterations=[
                [1, 1.2838, -230.42152688, -230.20919500, -7.11E-1, 2.07, 13, 3.58E-1, 1.39E-15, (1,1), 6354.45, 6354.45],
                [1, 1.3172, -230.44447074, -230.47744042, -5.54E-2, 3.20E-1, 13, 2.58E-1, 2.22E-15, None, 12693.51, 6346.76]
            ])

        self.assertEqual(parsedTable, expectedTable)


if __name__ == "__main__":
    unittest.main()
