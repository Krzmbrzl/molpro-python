from molpro import ParserData
from molpro import IterationTable


class RHF_Data(ParserData):
    def __init__(self):
        self.iterations: IterationTable = IterationTable()
        self.converged: bool = False
        self.energy: float = 0

    def associatedProgramName(self):
        return "RHF"
