from typing import Optional

from molpro import ParserData


class Program:
    def __init__(self, name: str = "<Undefined>", description: str = ""):
        self.name: str = name
        self.description: str = description
        self.output: Optional[ParserData] = None
