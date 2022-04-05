from typing import List
from typing import Iterator

from datetime import timedelta

from molpro import ProgramMetadata
from molpro import utils
from molpro import Duration

class ProgramMetadataParser:
    @staticmethod
    def parse(lines: List[str], lineIt: Iterator[int]) -> ProgramMetadata:
        # Skip to the metadata block
        utils.skip_to(lines, lineIt, startswith="*****************************************************")

        i = utils.skip_to(lines, lineIt, startswith="CPU TIMES")
        # The CPU times are listed individually for each program, but the first entry is always the total
        # CPU time, which we want to obtain
        cpuTime = float(utils.consume(lines[i], prefix="CPU TIMES  *").split()[0])

        i = utils.skip_to(lines, lineIt, startswith="REAL TIME")
        wallTime = float(utils.consume(lines[i], prefix="REAL TIME  *", gobble_from="SEC", strip=True))

        return ProgramMetadata(cpuTime=Duration(timedelta(seconds=cpuTime), Duration.Reference.CPU),
                wallTime=Duration(timedelta(seconds=wallTime), Duration.Reference.WALL))
