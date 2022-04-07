from typing import List
from typing import Any
from typing import Union


class IterationTable:
    def __init__(self, headers: List[str] = [], rows: List[List[Any]] = []):
        self.headers = headers
        self.rows = rows


    def iteration(self, it: int) -> List[Any]:
        # Iterations are 1-based indices
        return self.rows[it - 1]


    def column(self, key: Union[int, str]) -> List[Any]:
        if isinstance(key, str):
            try:
                key = self.headers.index(key)
            except ValueError:
                raise KeyError("Unknown data column \"" + key + "\"")

        column = [ x[key] for x in self.rows ]

        return column


    def __eq__(self, other):
        if isinstance(other, IterationTable):
            return self.headers == other.headers and self.rows == other.rows
        else:
            return False

    def __repr__(self):
        representation = "IterationTable(\n  columnHeaders=%r,\n  iterations=[\n" % self.rows
        for current in self.rows:
            representation += "    %r" % current + ",\n"
        if representation.endswith(",\n"):
            representation = representation[ : -2]

        representation += "\n  ]\n)"

        return representation

