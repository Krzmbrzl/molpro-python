from typing import List
from typing import Iterator
from typing import Optional

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

        iterationHeaderLine = utils.skip_to(lines, lineIt, startswith="ITER")

        headers = lines[iterationHeaderLine].split()
        expectedHeaders = ["ITER", "ETOT", "DE", "GRAD", "DDIFF",
                           "DIIS", "NEXP", "TIME(IT)", "TIME(TOT)", "DIAG"]

        if not headers == expectedHeaders:
            raise OutputFormatError("Expected column headers for RHF iterations to be %s but got %s" % (
                str(expectedHeaders), str(headers)))

        # TODO someday: Give alternate (more readable) names to columns (as alternative access keys)

        # Keep column headers as-is, except drop "ITER" column (we don't need that)
        headers.pop(0)

        data.iterations.columnHeaders = headers

        # Iterate over the different iterations
        for i in lineIt:
            entries = lines[i].split()

            if len(entries) == 0:
                # Empty line -> End of iterations
                break

            if not len(entries) == len(headers) + 1:
                raise OutputFormatError("Expected RHF iteration information to consist of %d parts but got %d" % (
                    len(headers) + 1, len(entries)))

            # remove first column ("ITER") as we don't need that
            entries.pop(0)

            # Convert the different columns into the proper data type
            entries = [float(entries[0]), float(entries[1]), float(entries[2].replace("D", "E")), float(entries[3].replace("D", "E")),
                       int(entries[4]), int(entries[5]), float(entries[6]), float(entries[7]), entries[8]]
            
            data.iterations.iterations.append(entries)


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
            data.convered = True

        # Skip to and read final energy
        energyLine = utils.skip_to(lines, lineIt, startswith="!RHF STATE")
        data.energy = float(utils.consume(lines[energyLine], prefix="!RHF STATE", gobble_until="Energy", strip=True))


        return data
