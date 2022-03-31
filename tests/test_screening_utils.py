#!/usr/bin/env python3

import unittest

from screening import utils


class TestScreeningUtils(unittest.TestCase):
    def test_combine_lists(self):
        A = []
        B = []
        C = utils.combine(A, B)
        expected = []
        self.assertEqual(C, expected)

        A = [["A"]]
        B = []
        C = utils.combine(A, B)
        expected = A
        self.assertEqual(C, expected)

        A = []
        B = [["B"]]
        C = utils.combine(A, B)
        expected = B
        self.assertEqual(C, expected)

        A = [["A"]]
        B = [["B"]]
        C = utils.combine(A, B)
        expected = [["A", "B"]]
        self.assertEqual(C, expected)

        A = [["A1"], ["A2"]]
        B = [["B"]]
        C = utils.combine(A, B)
        expected = [["A1", "B"], ["A2", "B"]]
        self.assertEqual(C, expected)

        A = [["A1"], ["A2"]]
        B = [["B", "C"], ["D"]]
        C = utils.combine(A, B)
        expected = [["A1", "B", "C"], ["A1", "D"],
                    ["A2", "B", "C"], ["A2", "D"]]
        self.assertEqual(C, expected)

        A = [["A1", "X"]]
        B = [["B", "C"], ["D"]]
        C = utils.combine(A, B)
        expected = [["A1", "X", "B", "C"], ["A1", "X", "D"]]
        self.assertEqual(C, expected)

    def test_combine_dicts(self):
        A = [{"A": "a"}]
        B = []
        C = utils.combine(A, B)
        expected = A
        self.assertEqual(C, expected)

        A = []
        B = [{"B": "b"}]
        C = utils.combine(A, B)
        expected = B
        self.assertEqual(C, expected)

        A = [{"A": "a"}]
        B = [{"B": "b"}]
        C = utils.combine(A, B)
        expected = [{"A": "a", "B": "b"}]
        self.assertEqual(C, expected)

        A = [{"A1": 1}, {"A2": 2}]
        B = [{"B": "b2"}]
        C = utils.combine(A, B)
        expected = [{"A1": 1, "B": "b2"}, {"A2": 2, "B": "b2"}]
        self.assertEqual(C, expected)

        A = [{"A1": 1}, {"A2": 2}]
        B = [{"B": "b", "C": "c"}, {"D": "d"}]
        C = utils.combine(A, B)
        expected = [{"A1": 1, "B": "b", "C": "c"}, {"A1": 1, "D": "d"}, {
            "A2": 2, "B": "b", "C": "c"}, {"A2": 2, "D": "d"}]
        self.assertEqual(C, expected)

        A = [{"A1": 1, "X": "x"}]
        B = [{"B": "b", "C": "c"}, {"D": "d"}]
        C = utils.combine(A, B)
        expected = [{"A1": 1, "X": "x", "B": "b", "C": "c"},
                    {"A1": 1, "X": "x", "D": "d"}]
        self.assertEqual(C, expected)
