from typing import Optional
from typing import Iterator
from typing import List
from typing import Tuple

from datetime import timedelta
import itertools

from molpro import ProgramParser
from molpro import ParserData
from molpro import MolproOutput
from molpro import register_program_parser
from molpro import CMRCC_Data
from molpro import utils
from molpro import OutputFormatError
from molpro import Duration


def name_spin_sym(nElec: int) -> str:
    names = ["Singlet", "Doublet", "Triplet", "Quartet",
             "Quintet", "Sextet", "Septet", "Octet", "Nonet", "Decet"]

    if nElec < len(names):
        return names[nElec]

    if nElec % 2:
        return "S=%d" % (nElec // 2)
    else:
        return "S=%d/2" % nElec


def parse_orbital_spec(spec: str) -> Tuple[int, List[int]]:
    # We expect the format to be e.g. "6 (   4   0   2   0 )" where the first number is the total
    # number of orbitals and the individual numbers in parenthesis are the orbitals per irreducible
    # representation.
    if not "(" in spec and ")" in spec:
        raise OutputFormatError(
            "CMRCC: Unexpected orbital specification format")

    begin = spec.find("(")
    end = spec.find(")")
    total = spec[: begin].strip()
    individual = spec[begin + 1: end].strip()

    return (int(total), [int(x) for x in individual.split()])


@register_program_parser
class CMRCC_Parser(ProgramParser):
    def __init__(self):
        super(ProgramParser, self).__init__()

    def parse(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput) -> Optional[ParserData]:
        data = CMRCC_Data()

        # We need to parse the "PROGRAM * ..." line to figure out whether this is the ITF-based (Molpro-internal) implementation
        # or the GeCCo interface
        description = utils.consume(lines[next(
            lineIt)], prefix="PROGRAM * CMRCC", gobble_until="(", gobble_from=")", strip=True)

        data.usedGeCCo = "GeCCo" in description

        if data.usedGeCCo:
            return self.parseGeCCo(lines, lineIt, output, data)
        else:
            return self.parseRegular(lines, lineIt, output, data)

    def parseRegular(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput, data: CMRCC_Data) -> CMRCC_Data:
        # Extract information about reference symmetry (spatial and spin)
        i = utils.skip_to(lines, lineIt, startswith="Reference symmetry:")
        symSpecs = utils.consume(
            lines[i], prefix="Reference symmetry:", strip=True).split()

        if len(symSpecs) != 2:
            raise OutputFormatError(
                "CMRCC reference symmetry spec is in unexpected format (%d parts instead of 2)" % len(symSpecs))

        data.space_symmetry = int(symSpecs[0])
        data.spin_symmetry = symSpecs[1]

        # Extract information about active space
        i = utils.skip_to(lines, lineIt, startswith="Number of core orbitals:")
        data.n_core_orbitals, data.core_orbitals = parse_orbital_spec(
            utils.consume(lines[i], prefix="Number of core orbitals:", strip=True))
        data.n_closed_orbitals, data.closed_orbitals = parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of closed-shell orbitals:", strip=True))
        # Note the double-blank after "active"
        data.n_active_orbitals, data.active_orbitals = parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of active  orbitals:", strip=True))
        data.n_external_orbitals, data.external_orbitals = parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of external orbitals:", strip=True))

        # Check for integral transformation
        i = utils.skip_to(lines, lineIt, contains="transformation")
        data.integral_transformation_performed = "Integral transformation finished" in lines[
            i]
        if data.integral_transformation_performed:
            cpuTime = float(utils.consume(
                lines[i], prefix="Integral transformation finished. Total CPU:", gobble_from="sec", strip=True))
            data.integral_transformation_duration = Duration(
                timedelta(seconds=cpuTime), Duration.Reference.CPU)

        # Read out p-space configurations
        i = utils.skip_to(
            lines, lineIt, startswith="Number of p-space configurations:")
        data.n_p_space_configrations = int(utils.consume(
            lines[i], prefix="Number of p-space configurations:", strip=True))

        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(
            lines, peekIt, startswith="Reference state will be relaxed", default=-1)
        data.reference_relaxation = i > 0

        # Parse iteration table
        utils.skip_to(lines, lineIt, startswith="Singular value threshold")
        next(lineIt)  # Skip empty line
        # Parse the actual iteration table. Note that the DIIS column is actually optional in the sense that
        # in a converged calculation, the last iteration will not have any entry in either DIIS column.
        data.iterations \
            = utils.parse_iteration_table(lines,
                                          lineIt, col_types=[
                                              [int, int, float, float, float, float, float, int,
                                                  float, float, (int, int), float, float],
                                              [int, int, float, float, float, float, float,
                                                  int, float, float, None, float, float]
                                          ], del_cols={"ITER"}, substitutions={"SV INCL": "SV_INCL", "SV EXCL": "SV_EXCL"})

        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(
            lines, peekIt, startswith="WARNING: Failed to converge", default=-1)
        if i != -1:
            output.errors.append("CMRCC calculation failed to converge")

        # Extract info about runtime
        i = utils.skip_to(lines, lineIt, startswith="Time per iteration")
        # The time is in format "Time per iteration:        6562.06 sec (CPU)   7335.87 sec (Wall)"
        cpuTime = utils.consume(
            lines[i], prefix="Time per iteration:", gobble_from="sec", strip=True)
        wallTime = utils.consume(
            lines[i], prefix="Time per iteration:", gobble_until=")", gobble_from="sec", strip=True)
        data.cpu_time_per_iteration = Duration(
            timedelta(seconds=float(cpuTime)), Duration.Reference.CPU)
        data.wall_time_per_iteration = Duration(
            timedelta(seconds=float(wallTime)), Duration.Reference.WALL)

        # Parse resulting state's energy
        i = utils.skip_to(lines, lineIt, startswith="Correlation energy:")
        data.correlation_energy = float(utils.consume(
            lines[i], prefix="Correlation energy:", strip=True))
        if data.reference_relaxation:
            i = utils.skip_to(lines, lineIt, startswith="Correlation energy",
                              contains="relative to relaxed reference")
            data.correlation_energy = float(utils.consume(
                lines[i], prefix="Correlation energy:", gobble_from="(", strip=True))
        i = utils.skip_to(lines, lineIt, startswith="!Total energy:")
        data.total_energy = float(utils.consume(
            lines[i], prefix="!Total energy:", strip=True))

        return data

    def parseGeCCo(self, lines: List[str], lineIt: Iterator[int], output: MolproOutput, data: CMRCC_Data) -> CMRCC_Data:
        # Extract information about active space
        i = utils.skip_to(lines, lineIt, startswith="Number of core orbitals:")
        data.n_core_orbitals, data.core_orbitals = parse_orbital_spec(
            utils.consume(lines[i], prefix="Number of core orbitals:", strip=True))
        data.n_closed_orbitals, data.closed_orbitals = parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of inactive orbitals:", strip=True))
        data.n_active_orbitals, data.active_orbitals = parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of active orbitals:", strip=True))
        data.n_external_orbitals, data.external_orbitals = parse_orbital_spec(
            utils.consume(lines[next(lineIt)], prefix="Number of virtual orbitals:", strip=True))

        # Get symmetry info
        i = utils.skip_to(lines, lineIt, startswith="wfu symmetry")
        data.space_symmetry = int(utils.consume(
            lines[i], prefix="wfu symmetry", gobble_until="=", strip=True))
        i = utils.skip_to(lines, lineIt, startswith="unpaired electrons")
        data.spin_symmetry = name_spin_sym(int(utils.consume(
            lines[i], prefix="unpaired electrons", gobble_until="=", strip=True)))

        # Integral transformation
        utils.skip_to(
            lines, lineIt, startswith="Generating transformed integrals")
        data.integral_transformation_performed = True
        i = utils.skip_to(lines, lineIt, startswith="Load integrals")
        time = float(utils.consume(
            lines[i], prefix="Load integrals", gobble_from="sec", strip=True))
        time += float(utils.consume(lines[next(lineIt)],
                      prefix="Transform integrals", gobble_from="sec", strip=True))
        data.integral_transformation_duration = Duration(
            timedelta(seconds=time), Duration.Reference.CPU)
        # Note that the above procedure won't work, if density-fitting was used as in this case the output will look different

        # Get to iteration table. Note that the relevant table is the second one
        utils.skip_to(lines, lineIt, startswith="ITER")
        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(lines, peekIt, startswith="ITER")
        utils.iterate_to(lineIt, i - 1)

        data.iterations = utils.parse_iteration_table(lines, lineIt,
                                                      col_types=[
                                                          [int, int, float, float, float, int, float, float, int, float, float]],
                                                      del_cols={"ITER."},
                                                      substitutions={"TOTAL ENERGY": "TOTAL_ENERGY", "ENERGY CHANGE": "ENERGY_CHANGE", "SV MIN": "SV_MIN", "SV MAX": "SV_MAX"})

        # Check for convergence
        lineIt, peekIt = itertools.tee(lineIt)
        i = utils.skip_to(lines, peekIt, startswith="CONVERGED", default=-1)
        if i < 0:
            output.errors.append("CMRCC (GeCCo) did not converge")


        # Fetch resulting energies
        # As it appears GeCCo will never do reference relaxation
        data.reference_relaxation = False
        i = utils.skip_to(lines, lineIt, startswith="Reference energy")
        refEnergy = float(utils.consume(lines[i], prefix="Reference energy", strip=True))
        i = utils.skip_to(lines, lineIt, startswith="Correlation energy")
        data.correlation_energy = float(utils.consume(lines[i], prefix="Correlation energy", strip=True))
        # The total energy is output in a strange format in the output, so we prefer to calculate it on-the-fly instead
        data.total_energy = data.correlation_energy + refEnergy

        return data