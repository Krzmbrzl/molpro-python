from typing import List

from molpro import MolproOutput
from molpro import utils
from molpro import ProgramParser
from molpro import MULTI_Data
from molpro import OutputFormatError

@ProgramParser.register_program_parser
class MULTI_Parser:
    def __init__(self):
        pass

    def parse(self, lines: List[str], begin: int, end: int, output: MolproOutput):
        data = MULTI_Data()
        
        i = utils.skip_to(lines, begin, startswith="Number of closed-shell orbitals")
        assert i < end

        data.closed_orbitals = int(utils.consume(lines[i], prefix="Number of closed-shell orbitals:", gobble_from="(", strip=True))
        i += 1
        assert i < end
        # Note the two consecutive blanks
        data.active_orbitals = int(utils.consume(lines[i], prefix="Number of active  orbitals:", gobble_from="(", strip=True))
        i += 1
        assert i < end
        data.external_orbitals = int(utils.consume(lines[i], prefix="Number of external orbitals:", gobble_from="(", strip=True))

        i = utils.skip_to(lines, i, startswith="Number of active electrons")
        assert i < end

        # This part is assumed to look like "Number of active electrons:   2    Spin symmetry=Singlet   Space symmetry=1"
        contentLine = utils.consume(lines[i], prefix="Number of active electrons:", strip=True)
        parts = contentLine.split()

        if not len(parts) == 5:
            raise OutputFormatError("Specification of active electrons etc. in MULTI output is in unexpected format")

        data.active_electrons = int(parts[0])

        if not "=" in parts[2]:
            raise OutputFormatError("Spin-state symmetry in MULTI output is in unexpected format")
        data.spin_symmetry = parts[2][parts[2].find("=") + 1 : ].strip()

        i = utils.skip_to(lines, i, startswith="Number of CSFs")
        assert i < end

        data.number_of_csfs = int(utils.consume(lines[i], prefix="Number of CSFs:", gobble_from="(", strip=True, optional_ops=["gobble_from"]))

        # Skip to actual iterations
        i = utils.skip_to(lines, i, startswith="ITER")
        assert i < end

        # Skip over iterations
        while i < end:
            if lines[i] == "":
                break
            
            i += 1

        i += 1
        assert i < end

        data.converged = lines[i].startswith("CONVERGENCE REACHED!")
        if not data.converged:
            output.errors.append("MULTI calculation failed to converge")

        return data


