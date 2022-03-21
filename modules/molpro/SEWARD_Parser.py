from typing import List
from typing import Iterator
from typing import Optional
import itertools

from molpro import MolproOutput
from molpro import utils
from molpro import ProgramParser
from molpro import register_program_parser
from molpro import ParserData
from molpro import SEWARD_Data


@register_program_parser
class SEWARD_Parser(ProgramParser):
    def __init__(self):
        super(ProgramParser, self).__init__()


    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
        data = SEWARD_Data()
        
        lineIt, lookaheadIt = itertools.tee(lineIt)

        moleculeLine = utils.skip_to(lines, lookaheadIt, startswith="Molecule type", default=-1)

        if moleculeLine >= 0:
            utils.iterate_to(lineIt, moleculeLine)

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
