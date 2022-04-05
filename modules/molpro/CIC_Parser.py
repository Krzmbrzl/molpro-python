from typing import Optional
from typing import Iterator
from typing import List

import itertools

from molpro import ProgramParser
from molpro import ParserData
from molpro import MolproOutput
from molpro import register_program_parser
from molpro import CIC_Data
from molpro import utils


@register_program_parser
class CIC_Parser(ProgramParser):
    def __init__(self):
        super(ProgramParser, self).__init__()

    def doParse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
        data = CIC_Data()

        # Extract information about active space
        i = utils.skip_to(lines, lineIt, startswith="Number of core orbitals:")
        data.n_core_orbitals, data.core_orbitals = utils.parse_orbital_spec(
            utils.consume(lines[i], prefix="Number of core orbitals:", strip=True))
        data.n_closed_orbitals, data.closed_orbitals = utils.parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of closed-shell orbitals:", strip=True))
        i = next(lineIt)
        if "active" in lines[i]:
            # Active orbitals are only listed for the open-shell case, so it's kinda optional
            # Note the double-blank after "active"
            data.n_active_orbitals, data.active_orbitals = utils.parse_orbital_spec(
                utils.consume(lines[i], prefix="Number of active  orbitals:", strip=True))
            i = next(lineIt)

        data.n_external_orbitals, data.external_orbitals = utils.parse_orbital_spec(
            utils.consume(lines[i], prefix="Number of external orbitals:", strip=True))

        # Parse iteration table
        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(lines, peekIt, startswith="ITER.")
        utils.iterate_to(lineIt, i - 1)

        data.iterations = utils.parse_iteration_table(lines, lineIt, col_types=[[int, float, float, float, float, float, float]],
                                                      substitutions={
                                                          "TOTAL ENERGY": "TOTAL_ENERGY", "ENERGY CHANGE": "ENERGY_CHANGE"},
                                                      del_cols={"ITER."})

        # Check for convergence
        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(
            lines, peekIt, startswith="WARNING: Failed to converge", default=-1)
        if i >= 0:
            data.converged = False
            output.errors.append("CIC failed to converge")
        else:
            data.converged = True

        # Parse final energy
        i = utils.skip_to(lines, lineIt, startswith="Correlation energy")
        data.correlation_energy = float(utils.consume(
            lines[i], prefix="Correlation energy", strip=True))
        i = utils.skip_to(lines, lineIt, startswith="!Total energy")
        data.total_energy = float(utils.consume(
            lines[i], prefix="!Total energy", strip=True))

        return data
