from datetime import timedelta
from enum import Enum

class Duration:
    class Reference(Enum):
        WALL = 0
        CPU = 1

    def __init__(self, duration: timedelta, reference: Reference):
        self.duration: timedelta = duration
        self.reference: Duration.Reference = reference
