from typing import List
from typing import Any
from typing import Union


class IterationTable:
    def __init__(self, columnHeaders: List[str] = [], iterations: List[List[Any]] = []):
        self.columnHeaders = columnHeaders
        self.iterations = iterations


    def iteration(self, it: int) -> List[Any]:
        # Iterations are 1-based indices
        return self.iterations[it - 1]


    def column(self, key: Union[int, str]) -> List[Any]:
        if isinstance(key, str):
            try:
                key = self.columnHeaders.index(key)
            except ValueError:
                raise KeyError("Unknown data column \"" + key + "\"")

        column = [ x[key] for x in self.iterations ]

        return column


    def __eq__(self, other):
        if isinstance(other, IterationTable):
            return self.columnHeaders == other.columnHeaders and self.iterations == other.iterations
        else:
            return False

    def __repr__(self):
        representation = "IterationTable(\n  columnHeaders=%r,\n  iterations=[\n" % self.columnHeaders
        for current in self.iterations:
            representation += "    %r" % current + ",\n"
        if representation.endswith(",\n"):
            representation = representation[ : -2]

        representation += "\n  ]\n)"

        return representation

