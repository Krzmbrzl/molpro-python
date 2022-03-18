from typing import List
import logging

import molpro
from molpro import MolproError
from molpro import OutputFormatError
from molpro import MolproOutput
from molpro import Node
from molpro import utils
from molpro import ProgramParser

logger = logging.getLogger("molpro.outputfileparser")


class OutputFileParser:
    def __init__(self):
        pass

    def parse(self, content, parse_details: bool = True) -> MolproOutput:
        try:
            # Assume content is a path
            content = open(content, "r")
        except TypeError:
            pass

        file = None
        try:
            try:
                # Assume content is a file
                file = content
                content = file.read()
            except TypeError:
                file = None

            # At this point we assume to have a string-type argument
            return self.__doParse(content, parse_details=parse_details)

        finally:
            # Close file, in case we opened it
            if not file is None:
                file.close()


    def __doParse(self, content: str, parse_details: bool = True) -> MolproOutput:
        output = MolproOutput()

        lines = [x.strip() for x in content.split("\n")]
        # Remove trailing blank lines
        while len(lines) > 0 and lines[-1] == "":
            lines.pop()


        lineIt = iter(range(len(lines)))
        # Skip leading blank lines
        for i in lineIt:
            if lines[i] == "":
                continue

            lineIt = iter(range(i, len(lines)))

            break

        # Parse general (working) directory information
        output.working_directory = utils.consume(
            lines[next(lineIt)], prefix="Working directory", gobble_until=":", strip=True)
        output.scratch_directory = utils.consume(lines[next(
            lineIt)], prefix="Global scratch directory", gobble_until=":", strip=True)
        output.wavefunction_directory = utils.consume(
            lines[next(lineIt)], prefix="Wavefunction directory", gobble_until=":", strip=True)
        output.input_file_directory = utils.consume(
            lines[next(lineIt)], prefix="Main file repository", gobble_until=":", strip=True)

        # Skip to nodes block
        lineIt = iter(range(utils.skip_to(lines, next(lineIt),
                      startswith="Nodes") + 1, len(lines)))

        # Parse node + processor count per node specifications
        for i in lineIt:
            parts = lines[i].split()

            # We expect these lines to be in format <nodeName> <nProcs>
            if len(parts) != 2:
                break

            output.nodes.append(Node(parts[0], int(parts[1])))

        if not len(output.nodes) > 0:
            raise OutputFormatError(
                "Couldn't read node specification from output")

        # Skip to input definition
        lineIt = iter(range(utils.skip_to(lines, next(lineIt),
                      startswith="Variables initialized") + 1, len(lines)))

        # Read and re-assemble the original Molpro input
        molproInput = ""
        for i in lineIt:
            if lines[i].startswith("Commands initialized"):
                break
            else:
                molproInput += lines[i] + "\n"

        output.input_definition = molproInput.strip()

        # Skip to input checking result
        lineIt = iter(range(utils.skip_to(lines, next(lineIt),
                      startswith="Checking input...") + 1, len(lines)))

        if lines[next(lineIt)] != "Passed":
            output.errors.append("Input verification failed")
            return output

        # Skip to version specification and parse that
        lineIt = iter(range(utils.skip_to(lines, next(lineIt),
                      startswith="Version"), len(lines)))
        output.version = utils.consume(
            lines[next(lineIt)], prefix="Version", gobble_from="linked", strip=True)

        # Skip to version hash specification and parse that
        lineIt = iter(
            range(utils.skip_to(lines, next(lineIt), startswith="SHA1:"), len(lines)))
        output.version_hash = utils.consume(
            lines[next(lineIt)], prefix="SHA1:", strip=True)

        # Skip to threshold specifications
        index = utils.skip_to(lines, next(lineIt),
                              startswith="THRESHOLDS:")
        if index < len(lines):
            lineIt = iter(range(index + 1, len(lines)))

            for i in lineIt:
                if lines[i] == "":
                    if len(output.thresholds) == 0:
                        # Skip empty lines between "THRESHOLDS" header and actual specs
                        continue
                    else:
                        # Empty lines encountered after the first thresholds have been parsed, indicate the end of the spec block
                        break

                parts = lines[i].replace("=", " = ").split()
                if not len(parts) % 3 == 0:
                    raise OutputFormatError(
                        "Expected threshold specification to occur in triples (name = value)")

                # Iterate over triples <name> = <value>
                for k in range(len(parts) // 3):
                    if not parts[k * 3 + 1] == "=":
                        raise OutputFormatError(
                            "Threshold specification is not using the \"=\" character in the expected way")

                    output.thresholds[parts[k * 3]
                                      ] = float(parts[k * 3 + 2].replace("D", "E"))

        # Iterate over the different program parts and parse them using the dedicated parsers
        lineIt = iter(range(utils.skip_to(lines, next(lineIt),
                      startswith="PROGRAM *"), len(lines)))

        programOutputIntervals = []
        currentIntervalStart = -1

        for i in lineIt:
            if lines[i].startswith("PROGRAM *"):
                # Begin of new program output
                if currentIntervalStart >= 0:
                    # There has been a previous interval -> finish it
                    programOutputIntervals.append(
                        (currentIntervalStart, i - 1))
                # Start the new interval
                currentIntervalStart = i
            elif lines[i].startswith("?"):
                try:
                    newIndex = self.__processErrorOrWarning(lines, i, output)
                    while i < newIndex:
                        i = next(lineIt)
                except MolproError:
                    # The __processErrorOrWarning function has failed -> Assume that this is an error in non-standard format then
                    output.errors.append(lines[i][1 : ].strip())
            elif lines[i].startswith("GLOBAL ERROR"):
                output.errors.append(lines[i])

        if currentIntervalStart < 0:
            raise OutputFormatError(
                "Didn't find the output of a single program")

        # Finish last interval
        programOutputIntervals.append((currentIntervalStart, len(lines) - 1))

        if parse_details:
            # Iterate over and parse individual program blocks
            for begin, end in programOutputIntervals:
                programSpec = utils.consume(
                    lines[begin], prefix="PROGRAM *", gobble_after=")", strip=True)

                index = programSpec.find("(")
                programName = programSpec[: index].strip()
                programDescription = programSpec[index + 1: -1].strip()

                if programName == "" or programDescription == "":
                    raise OutputFormatError(
                        "Program name and/or description in unexpected format: %s" % programSpec)

                parserName = programName.lower() + "_parser"
                if not parserName in ProgramParser.program_parsers:
                    logger.warning(
                        "Skipping output of program \"%s\" as no parser for it is available" % programName)
                else:
                    # Use dedicated parser to make sense of the program's output
                    parser = ProgramParser.program_parsers[parserName]()

                    parsedOutput = parser.parse(lines, begin, end, output)

                    if not parsedOutput is None:
                        output.program_outputs.append(parsedOutput)

        output.calculation_finished = lines[-1] == "Molpro calculation terminated"

        return output


    def __processErrorOrWarning(self, lines: List[str], index: int, output: MolproOutput):
        severity = utils.consume(lines[index], prefix="?", strip=True)
        index += 1
        message = utils.consume(lines[index], prefix="?", strip=True)
        index += 1
        location = utils.consume(lines[index], prefix="?", strip=True)
        location = utils.consume(location, prefix="The problem occurs in", strip=True)

        completeMsg = message + " (in " + location + ")"

        if severity.lower() == "warning":
            output.warnings.append(completeMsg)
        else:
            output.errors.append(completeMsg)

        return index
