from typing import List
from typing import Iterator

from molpro import MolproOutput
from molpro import utils
from molpro import ProgramParser
from molpro import ParserData
from molpro import SEWARD_Data


@ProgramParser.register_program_parser
class SEWARD_Parser:
    def __init__(self):
        pass

    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> ParserData:
        data = SEWARD_Data()

        moleculeLine = utils.skip_to(lines, lineIt, startswith="Molecule type")

        data.molecule_type = utils.consume(
            lines[moleculeLine], prefix="Molecule type:", strip=True)

        groupLine = utils.skip_to(lines, lineIt, startswith="Point group")

        output.point_group = utils.consume(
            lines[groupLine], prefix="Point group", strip=True)

        contractionsLine = utils.skip_to(
            lines, lineIt, startswith="NUMBER OF CONTRACTIONS")

        data.basis_set_size = int(utils.consume(
            lines[contractionsLine], prefix="NUMBER OF CONTRACTIONS:", gobble_from="(", strip=True))

        return data
