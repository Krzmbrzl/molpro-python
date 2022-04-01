from typing import List
from typing import Iterator
from typing import Optional
from typing import Tuple
from typing import Dict
import itertools

from molpro import MolproOutput
from molpro import utils
from molpro import ProgramParser
from molpro import register_program_parser
from molpro import ParserData
from molpro import MULTI_Data
from molpro import OutputFormatError


def get_mcscf_columns(mcscfType: str) -> Tuple[List[str], List[List[type]], Dict[str, str]]:
    colNames = []
    colTypes = []
    substitutions = {}

    if mcscfType == "First-order MCSCF: SO-SCI":
        colNames = ["ITER.", "MIC", "NCI", "ENERGY", "ENERGY_CHANGE",
                    "GRAD", "ORB_GRAD", "CI_RES", "NQN", "STEP", "TIME"]
        colTypes = [int, int, int, float, float,
                    float, float, float, int, float, float]
        substitutions = {"ENERGY CHANGE": "ENERGY_CHANGE",
                         "ORB GRAD": "ORB_GRAD", "CI RES": "CI_RES"}
    elif mcscfType == "Second-order MCSCF: L-BFGS accelerated":
        colNames = ["ITER", "MIC", "NCI", "NEG",
                    "ENERGY(VAR)", "ENERGY(PROJ)", "ENERGY_CHANGE", "GRAD(0)", "GRAD(ORB)", "GRAD(CI)", "STEP", "TIME"]
        colTypes = [int, int, int, int, float, float,
                    float, float, float, float, float, float]
        substitutions = {"ENERGY CHANGE": "ENERGY_CHANGE"}
    else:
        raise OutputFormatError("Unknown MCSCF type \"%s\"" % (mcscfType))

    return colNames, [colTypes], substitutions


@register_program_parser
class MULTI_Parser(ProgramParser):
    def __init__(self):
        super(ProgramParser, self).__init__()

    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
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

        if not "=" in parts[4]:
            raise OutputFormatError(
                "Space symmetry in MULTI output is in unexpected format")
        data.space_symmetry = int(parts[4][parts[4].find("=") + 1:])

        i = utils.skip_to(lines, lineIt, startswith="Number of CSFs")

        data.number_of_csfs = int(utils.consume(
            lines[i], prefix="Number of CSFs:", gobble_from="(", strip=True, optional_ops=["gobble_from"]))

        # Skip to actual iterations, but in such a way that we don't consume the headline yet
        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(lines, peekIt, startswith="ITER")

        utils.iterate_to(lineIt, i - 3)

        mcscfType = lines[next(lineIt)].strip()
        if mcscfType == "":
            raise OutputFormatError(
                "Failed to find MCSCF-type line in MULTI output")

        expectedHeaders, columnTypes, substitutions = get_mcscf_columns(
            mcscfType)

        assert "ITER" in expectedHeaders[0], "Assumed first column in MULTI iterations to represent iteration count"

        # Skip blank line
        next(lineIt)

        # Parse the iterations
        table = utils.parse_iteration_table(lines, lineIt, col_types=columnTypes, del_cols={
                                            expectedHeaders[0]}, substitutions=substitutions)
        # Make sure to also remove the ITER column from the expected headers, before comparing it with the parsed result
        expectedHeaders.pop(0)
        if not table.columnHeaders == expectedHeaders:
            raise OutputFormatError(
                "Expected MULTI iterations header to be %s but got %s" % (expectedHeaders, table.columnHeaders))

        data.iterations = table

        data.converged = lines[next(lineIt)].startswith("CONVERGENCE REACHED!")
        if not data.converged:
            output.errors.append("MULTI calculation failed to converge")

        return data
