
from typing import Optional
from typing import Iterator
from typing import List

import itertools

from molpro import ProgramParser
from molpro import ParserData
from molpro import MolproOutput
from molpro import register_program_parser
from molpro import CCSD_Data
from molpro import utils


@register_program_parser
class CCSD_Parser(ProgramParser):
    def __init__(self):
        super(ProgramParser, self).__init__()

    def doParse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
        data = CCSD_Data()

        # We need to parse the "PROGRAM * ..." line to figure out whether this is the open-shell or closed-shell implementation
        description = utils.consume(lines[next(
            lineIt)], prefix="PROGRAM * CCSD", gobble_until="(", gobble_from=")", strip=True)
        data.closed_shell = "Closed-shell" in description

        # Parse orbital information
        i = utils.skip_to(lines, lineIt, startswith="Number of core orbitals:")
        data.n_core_orbitals, data.core_orbitals = utils.parse_orbital_spec(
            utils.consume(lines[i], prefix="Number of core orbitals:", strip=True))
        data.n_closed_orbitals, data.closed_orbitals = utils.parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of closed-shell orbitals:", strip=True))
        if not data.closed_shell:
            # Active orbitals are only listed for the open-shell case, so it's kinda optional
            # Note the double-blank after "active"
            data.n_active_orbitals, data.active_orbitals = utils.parse_orbital_spec(
                utils.consume(lines[next(lineIt)], prefix="Number of active  orbitals:", strip=True))

        data.n_external_orbitals, data.external_orbitals = utils.parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of external orbitals:", strip=True))

        # Skip to iteration table
        if data.closed_shell:
            lineIt, peekIt = itertools.tee(lineIt)
            i = utils.skip_to(lines, peekIt, startswith="ITER.")
            utils.iterate_to(lineIt, i - 1)
        else:
            # In UCCSD the first iteration table in the output is the one for a preceding RMP2 calculation
            # We want to ignore that one
            utils.skip_to(lines, lineIt, startswith="Starting UCC")
            # Skip blank line
            next(lineIt)

        # Parse iteration table
        substitutions = {"TOTAL ENERGY": "TOTAL_ENERGY",
                         "ENERGY CHANGE": "ENERGY_CHANGE"}
        if data.closed_shell:
            expectedColTypes = [int, float, float, float, float,
                                float, float, float, (int, int), float, float]
        else:
            # The open-shell iteration table is missing the time/it column from the closed-shell case
            expectedColTypes = [int, float, float, float,
                                float, float, float, float, (int, int), float]

        data.iterations = utils.parse_iteration_table(lines, lineIt, col_types=[
                                                      expectedColTypes], substitutions=substitutions, del_cols={"ITER."})

        # Check for convergence
        if data.closed_shell:
            lineIt, peekIt = itertools.tee(lineIt)
            data.converged = utils.skip_to(
                lines, peekIt, startswith="?CONVERGENCE NOT REACHED", default=-1) == -1
        else:
            lineIt, peekIt = itertools.tee(lineIt)
            data.converged = utils.skip_to(
                lines, peekIt, contains="NO CONVERGENCE", default=-1) == -1

        if not data.converged:
            output.errors.append("CCSD calculation failed to converge")

        # Parse final energies
        i = utils.skip_to(lines, lineIt, contains="correlation energy")
        # The first word in this line will be the used method's name (e.g. "CCD correlation energy")
        data.method = lines[i].split()[0]
        data.correlation_energy = float(utils.consume(
            lines[i], gobble_until="correlation energy", strip=True))

        # Note that while the closed-shell variant explicitly writes "total energy", the open-shell variant merely
        # write "energy" into the output. In order to treat both, we simply assume that the energy specified after
        # the correlation energy will be the total energy.
        i = utils.skip_to(lines, lineIt, contains="energy")
        data.total_energy = float(utils.consume(
            lines[i], gobble_until="energy", strip=True))

        return data
