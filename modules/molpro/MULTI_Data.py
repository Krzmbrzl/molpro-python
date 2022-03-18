from typing import Optional

from molpro import ParserData


class MULTI_Data(ParserData):
    def __init__(self):
        self.closed_orbitals: int = -1
        self.active_orbitals: int = -1
        self.external_orbitals: int = -1
        self.active_electrons: int = -1
        self.spin_symmetry: Optional[str] = None
        self.number_of_csfs: int = -1
        self.converged: bool = False

    def associatedProgrameName(self):
        return "MULTI"
