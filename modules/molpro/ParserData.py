from typing import Optional

from molpro import ProgramMetadata

class ParserData:
    def __init__(self):
        self.metadata: Optional[ProgramMetadata] = None


    def associatedProgrameName(self):
        raise RuntimeError("This function should have been implemented by subclasses")
