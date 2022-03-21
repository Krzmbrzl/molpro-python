from typing import Optional
from typing import List
from typing import Iterator
from typing import Dict
from typing import Type

from molpro import ParserData
from molpro import MolproOutput


class ProgramParser:
    def __init__(self):
        pass

    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
        raise RuntimeError(
            "This function should have been implemeted by a subclass")


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
