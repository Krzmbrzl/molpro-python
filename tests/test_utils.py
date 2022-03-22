#!/usr/bin/env python3

import unittest

from molpro import IterationTable

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


if __name__ == "__main__":
    unittest.main()

