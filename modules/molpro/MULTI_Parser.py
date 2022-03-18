from typing import List
from typing import Iterator

from molpro import MolproOutput
from molpro import utils
from molpro import ProgramParser
from molpro import ParserData
from molpro import MULTI_Data
from molpro import OutputFormatError


@ProgramParser.register_program_parser
class MULTI_Parser:
    def __init__(self):
        pass

    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> ParserData:
        data = MULTI_Data()

        i = utils.skip_to(
            lines, lineIt, startswith="Number of closed-shell orbitals")

        data.closed_orbitals = int(utils.consume(
            lines[i], prefix="Number of closed-shell orbitals:", gobble_from="(", strip=True))

        i = next(lineIt)
        # Note the two consecutive blanks
        data.active_orbitals = int(utils.consume(
            lines[i], prefix="Number of active  orbitals:", gobble_from="(", strip=True))

        i = next(lineIt)
        data.external_orbitals = int(utils.consume(
            lines[i], prefix="Number of external orbitals:", gobble_from="(", strip=True))

        i = utils.skip_to(
            lines, lineIt, startswith="Number of active electrons")

        # This part is assumed to look like "Number of active electrons:   2    Spin symmetry=Singlet   Space symmetry=1"
        contentLine = utils.consume(
            lines[i], prefix="Number of active electrons:", strip=True)
        parts = contentLine.split()

        if not len(parts) == 5:
            raise OutputFormatError(
                "Specification of active electrons etc. in MULTI output is in unexpected format")

        data.active_electrons = int(parts[0])

        if not "=" in parts[2]:
            raise OutputFormatError(
                "Spin-state symmetry in MULTI output is in unexpected format")
        data.spin_symmetry = parts[2][parts[2].find("=") + 1:].strip()

        i = utils.skip_to(lines, lineIt, startswith="Number of CSFs")

        data.number_of_csfs = int(utils.consume(
            lines[i], prefix="Number of CSFs:", gobble_from="(", strip=True, optional_ops=["gobble_from"]))

        # Skip to actual iterations
        i = utils.skip_to(lines, lineIt, startswith="ITER")

        # Skip over iterations
        while lines[next(lineIt)] != "":
            pass

        data.converged = lines[next(lineIt)].startswith("CONVERGENCE REACHED!")
        if not data.converged:
            output.errors.append("MULTI calculation failed to converge")

        return data
