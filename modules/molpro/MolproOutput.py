from typing import Optional
from typing import List
from typing import Dict

from molpro import Node
from molpro import Program


class MolproOutput:
    def __init__(self):
        self.working_directory: Optional[str] = None
        self.scratch_directory: Optional[str] = None
        self.wavefunction_directory: Optional[str] = None
        self.input_file_directory: Optional[str] = None

        self.nodes: List[Node] = []

        self.input_definition: Optional[str] = None

        self.errors: List[str] = []
        self.warnings: List[str] = []

        self.version: Optional[str] = None
        self.version_hash: Optional[str] = None

        self.thresholds: Dict[str, float] = {}

        self.calculation_finished: bool = False

        self.point_group: Optional[str] = None

        self.programs: List[Program] = []
