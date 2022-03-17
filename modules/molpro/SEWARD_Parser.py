from typing import List

from molpro import MolproOutput
from molpro import utils
from molpro import ProgramParser
from molpro import SEWARD_Data

@ProgramParser.register_program_parser
class SEWARD_Parser:
    def __init__(self):
        pass

    def parse(self, lines: List[str], begin: int, end: int, output: MolproOutput):
        data = SEWARD_Data()

        i = utils.skip_to(lines, begin, startswith="Molecule type")
        assert i < end

        data.molecule_type = utils.consume(lines[i], prefix="Molecule type:", strip=True)

        i = utils.skip_to(lines, i, startswith="Point group")
        assert i < end

        output.point_group = utils.consume(lines[i], prefix="Point group", strip=True)

        i = utils.skip_to(lines, i, startswith="NUMBER OF CONTRACTIONS")
        assert i < end

        data.basis_set_size = int(utils.consume(lines[i], prefix="NUMBER OF CONTRACTIONS:", gobble_from="(", strip=True))

        return data
