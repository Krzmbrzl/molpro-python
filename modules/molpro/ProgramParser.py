from typing import Optional
from typing import List
from typing import Iterator
from typing import Dict
from typing import Type

import itertools

from molpro import ParserData
from molpro import MolproOutput
from molpro import ProgramMetadataParser


class ProgramParser:
    def __init__(self):
        pass

    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> ParserData:
        lineIt, copyIt = itertools.tee(lineIt)

        data = self.doParse(lines, lineIt, output)

        data.metadata = ProgramMetadataParser.parse(lines, copyIt)

        return data

    def doParse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> ParserData:
        del lines
        del lineIt
        del output
        raise RuntimeError(
            "This function should have been implemented by a subclass")


program_parsers: Dict[str, Type[ProgramParser]] = {}
substitutions: Dict[str, str] = {
    "restricted hartree-fock_parser": "rhf_parser"
}


def register_program_parser(cls):
    program_parsers[cls.__name__.lower()] = cls
    return cls


def get_program_parser(name: str) -> Optional[ProgramParser]:
    if not name in program_parsers:
        if name in substitutions:
            subst = substitutions[name]
            return get_program_parser(subst)
        else:
            return None
    else:
        # Return an instance of the respective class
        return program_parsers[name]()
