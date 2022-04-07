from typing import Optional
from typing import List

from molpro import ParserData
from molpro import IterationTable


class CCSD_Data(ParserData):
    def __init__(self):
        self.method: Optional[str] = None
        self.closed_shell: bool = False
        self.n_core_orbitals: int = -1
        self.n_closed_orbitals: int = -1
        self.n_active_orbitals: Optional[int] = None
        self.n_external_orbitals: int = -1
        self.core_orbitals: List[int] = []
        self.closed_orbitals: List[int] = []
        self.active_orbitals: Optional[List[int]] = None
        self.external_orbitals: List[int] = []
        self.iterations: IterationTable = IterationTable()
        self.converged: bool = False
        self.total_energy: float = 0
        self.correlation_energy: float = 0

    def associatedProgramName(self):
        return "CCSD"
