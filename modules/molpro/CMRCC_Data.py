from typing import Optional
from typing import List

from molpro import ParserData
from molpro import IterationTable
from molpro import Duration


class CMRCC_Data(ParserData):
    def __init__(self):
        self.usedGeCCo: bool = False
        self.iterations: IterationTable = IterationTable()
        self.space_symmetry: int = -1
        self.spin_symmetry: Optional[str] = None
        self.n_core_orbitals: int = -1
        self.n_closed_orbitals: int = -1
        self.n_active_orbitals: int = -1
        self.n_external_orbitals: int = -1
        self.core_orbitals: List[int] = []
        self.closed_orbitals: List[int] = []
        self.active_orbitals: List[int] = []
        self.external_orbitals: List[int] = []
        self.integral_transformation_performed: bool = False
        self.integral_transformation_duration: Optional[Duration] = None
        self.n_p_space_configrations: Optional[int] = None
        self.cpu_time_per_iteration: Optional[Duration] = None
        self.wall_time_per_iteration: Optional[Duration] = None
        self.reference_relaxation: bool = False
        self.correlation_energy: float = 0
        self.correlation_energy_relaxed: Optional[float] = None
        self.total_energy: float = 0

    def associatedProgramName(self):
        return "CMRCC"
