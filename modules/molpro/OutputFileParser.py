from typing import List
from typing import Optional
import logging
import itertools
import os

from molpro import MolproError
from molpro import OutputFormatError
from molpro import MolproOutput
from molpro import Node
from molpro import utils
from molpro import get_program_parser
from molpro import Program
from molpro import ProgramParser
from molpro import Duration

logger = logging.getLogger("molpro.outputfileparser")


class OutputFileParser:
    def __init__(self):
        self.output = MolproOutput()

    def parse(self, content) -> MolproOutput:
        """Parse the given content and return a MolproOutput object representing the parsed result. The given
        content can either be a file-path, a file handle or just the literal content to be parsed."""
        # Reset output object
        self.output = MolproOutput()

        try:
            # Assume content is a path
            if len(content) < os.pathconf("/", "PC_PATH_MAX"):
                content = open(content, "r")
        except (TypeError, FileNotFoundError):
            pass

        file = None
        try:
            try:
                # Assume content is a file
                file = content
                content = file.read()
            except AttributeError:
                file = None

            # At this point we assume to have a string-type argument
            try:
                self.__doParse(content)
            except StopIteration:
                # The output was ended at an unexpected position. This could either mean that the output is from a running
                # calculation that just hasn't produced the remaining output yet or that an error occurred and the
                # output was cut off because of that.
                # In either case, we don't want this to crash our application and instead return the output object as parsed
                # so-far.
                pass

            return self.output

        finally:
            # Close file, in case we opened it
            if not file is None:
                file.close()

    def __doParse(self, content: str) -> None:
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
        self.output.working_directory = utils.consume(
            lines[next(lineIt)], prefix="Working directory", gobble_until=":", strip=True)
        self.output.scratch_directory = utils.consume(lines[next(
            lineIt)], prefix="Global scratch directory", gobble_until=":", strip=True)
        self.output.wavefunction_directory = utils.consume(
            lines[next(lineIt)], prefix="Wavefunction directory", gobble_until=":", strip=True)
        self.output.input_file_directory = utils.consume(
            lines[next(lineIt)], prefix="Main file repository", gobble_until=":", strip=True)

        # Skip to nodes block
        utils.skip_to(lines, lineIt, startswith="Nodes")

        # Parse node + processor count per node specifications
        for i in lineIt:
            parts = lines[i].split()

            # We expect these lines to be in format <nodeName> <nProcs>
            if len(parts) != 2:
                break

            self.output.nodes.append(Node(parts[0], int(parts[1])))

        if not len(self.output.nodes) > 0:
            # If we can step lineIt, that means that we did indeed fail to parse a node spec. However, if
            # we reached EOF between the "Nodes" header and where the actual specs should be, then stepping
            # the iterator will raise StopIteration, which is handled in the calling function (In this case,
            # we don't want to raise a format exception as most likely the output is just WIP)
            next(lineIt)
            raise OutputFormatError(
                "Couldn't read node specification from output")

        # Skip to input definition
        utils.skip_to(lines, lineIt, startswith="Variables initialized")

        # Read and re-assemble the original Molpro input
        molproInput = ""
        for i in lineIt:
            if lines[i].startswith("Commands initialized"):
                break
            else:
                molproInput += lines[i] + "\n"

        self.output.input_definition = molproInput.strip()

        # Skip to input checking result
        utils.skip_to(lines, lineIt, startswith="Checking input...")

        if lines[next(lineIt)] != "Passed":
            self.output.errors.append("Input verification failed")
            return

        # Skip to version specification and parse that
        versionLine = utils.skip_to(lines, lineIt, startswith="Version")
        self.output.version = utils.consume(
            lines[versionLine], prefix="Version", gobble_from="linked", strip=True)

        # Skip to version hash specification and parse that
        shaLine = utils.skip_to(lines, lineIt, startswith="SHA1:")
        self.output.version_hash = utils.consume(
            lines[shaLine], prefix="SHA1:", strip=True)

        # Skip to threshold specifications
        lineIt, lookaheadIt = itertools.tee(lineIt)
        thresholdLine = utils.skip_to(
            lines, lookaheadIt, startswith="THRESHOLDS:", default=-1)
        if thresholdLine >= 0:
            lineIt = iter(range(thresholdLine + 1, len(lines)))

            for i in lineIt:
                if lines[i] == "":
                    if len(self.output.thresholds) == 0:
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

                    self.output.thresholds[parts[k * 3]
                                           ] = float(parts[k * 3 + 2].replace("D", "E"))

        # Iterate over the different program parts and parse them using the dedicated parsers
        lineIt = iter(range(utils.skip_to(lines, lineIt,
                      startswith="PROGRAM *", case_sensitive=False), len(lines)))

        programOutputIntervals = []
        currentIntervalStart = -1

        for i in lineIt:
            if lines[i].lower().startswith("program *"):
                # Begin of new program output
                if currentIntervalStart >= 0:
                    # There has been a previous interval -> finish it
                    programOutputIntervals.append(
                        (currentIntervalStart, i))
                # Start the new interval
                currentIntervalStart = i
            elif lines[i].startswith("?"):
                try:
                    newIndex = self.__processErrorOrWarning(lines, i)
                    while i < newIndex:
                        i = next(lineIt)
                except MolproError:
                    # The __processErrorOrWarning function has failed -> Assume that this is an error in non-standard format then
                    self.output.errors.append(lines[i][1:].strip())
            elif lines[i].startswith("GLOBAL ERROR"):
                self.output.errors.append(lines[i])

        if currentIntervalStart < 0:
            raise OutputFormatError(
                "Didn't find the output of a single program")

        # Finish last interval
        programOutputIntervals.append((currentIntervalStart, len(lines) - 1))

        self.output.calculation_finished = lines[-1] == "Molpro calculation terminated"

        if len(self.output.errors) == 0:
            # Iterate over and parse individual program blocks, but only if we haven't encountered
            # any errors so far. If we did, chances are that the output of the individual programs is
            # corrupted and in order to avoid additional format exception, we rather not try parsing it.
            for i in range(len(programOutputIntervals)):
                begin, end = programOutputIntervals[i]

                programSpec = utils.consume(
                    lines[begin], prefix="PROGRAM *", gobble_after=")", strip=True, case_sensitive=False, optional_ops=["gobble_after"])

                index = programSpec.find("(")
                if index < 0:
                    # If no parenthesis are present, then assume that everything is the name and no description is given
                    programName = programSpec.strip()
                    programDescription = ""
                else:
                    programName = programSpec[: index].strip()
                    programDescription = programSpec[index + 1: -1].strip()

                if programName == "":
                    raise OutputFormatError(
                        "Program name in unexpected format: %s" % programSpec)

                program = Program(name=programName, description=programDescription)

                parserName = programName.lower() + "_parser"
                parser: Optional[ProgramParser] = get_program_parser(parserName)
                if parser is None:
                    logger.warning(
                        "Skipping output of program \"%s\" as no parser for it is available" % programName)
                else:
                    # Use dedicated parser to make sense of the program's output
                    subIt = iter(range(begin, end))

                    try:
                        program.output = parser.parse(lines, subIt, self.output)
                    except StopIteration:
                        if i < len(programOutputIntervals) - 1 or self.output.calculation_finished:
                            # Only the parsing of the last program output in an unfinished calculation may
                            # raise a StopIteration
                            logger.exception(
                                "Parsing the output of the \"%s\" program unexpectedly ran into EOF" % programName)

                self.output.programs.append(program)

            for i in range(len(self.output.programs)):
                if self.output.programs[i].output is None:
                    continue
                if i == 0:
                    self.output.programs[i].output.metadata.cpu_time = self.output.programs[i].output.metadata.total_cpu_time_so_far
                    self.output.programs[i].output.metadata.wall_time = self.output.programs[i].output.metadata.total_wall_time_so_far
                elif not self.output.programs[i - 1].output is None:
                    cpuTime = self.output.programs[i].output.metadata.total_cpu_time_so_far.duration - \
                        self.output.programs[i - 1].output.metadata.total_cpu_time_so_far.duration
                    wallTime = self.output.programs[i].output.metadata.total_wall_time_so_far.duration - \
                        self.output.programs[i - 1].output.metadata.total_wall_time_so_far.duration

                    self.output.programs[i].output.metadata.cpu_time = Duration(cpuTime, Duration.Reference.CPU)
                    self.output.programs[i].output.metadata.wall_time = Duration(wallTime, Duration.Reference.WALL)

    def __processErrorOrWarning(self, lines: List[str], index: int) -> int:
        try:
            severity = utils.consume(lines[index], prefix="?", strip=True)
            index += 1
            message = utils.consume(lines[index], prefix="?", strip=True)
            index += 1
            location = utils.consume(lines[index], prefix="?", strip=True)
            location = utils.consume(
                location, prefix="The problem occurs in", strip=True)
        except IndexError:
            # If we run into an IndexError, that means we have encountered an EOF in the middle of an error/warning
            # message block. Propagate this as if we ran into EOF using an iterator
            raise StopIteration()

        completeMsg = message + " (in " + location + ")"

        if severity.lower() == "warning":
            self.output.warnings.append(completeMsg)
        else:
            self.output.errors.append(completeMsg)

        return index
