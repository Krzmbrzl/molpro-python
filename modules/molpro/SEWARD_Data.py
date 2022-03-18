from typing import Optional

from molpro import ParserData


class SEWARD_Data(ParserData):
    def __init__(self):
        self.molecule_type: Optional[str] = None
        self.basis_set_size: int = -1

    def associatedProgrameName(self):
        return "SEWARD"



