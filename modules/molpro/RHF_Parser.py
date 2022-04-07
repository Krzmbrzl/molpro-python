from typing import List
from typing import Iterator
from typing import Optional

import itertools

from molpro import ProgramParser
from molpro import register_program_parser
from molpro import utils
from molpro import RHF_Data
from molpro import OutputFormatError
from molpro import MolproOutput
from molpro import ParserData


@register_program_parser
class RHF_Parser(ProgramParser):
    def __init__(self):
        super(ProgramParser, self).__init__()


    def doParse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
        data = RHF_Data()

        lineIt, peekIt = itertools.tee(lineIt)

        i = utils.skip_to(lines, peekIt, startswith="ITER")

        utils.iterate_to(lineIt, i - 1)

        data.iterations = utils.parse_iteration_table(lines, lineIt,
                col_types=[[int, float, float, float, float, int, int, float, float, str]],
                del_cols={"ITER"})

        # Skip empty lines
        followingLine = next(lineIt)
        while lines[followingLine].strip() == "":
            followingLine = next(lineIt)

        if lines[followingLine].startswith("?"):
            # We assume that this is an error stating that RHF didn't converge
            utils.consume(lines[followingLine], prefix="?No convergence in rhfpr")
            data.converged = False

            output.errors.append("RHF failed to converge")
        else:
            data.converged = True

        # Skip to and read final energy
        energyLine = utils.skip_to(lines, lineIt, startswith="!RHF STATE")
        data.energy = float(utils.consume(lines[energyLine], prefix="!RHF STATE", gobble_until="Energy", strip=True))


        return data
