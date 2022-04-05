from molpro import Duration

class ProgramMetadata:
    def __init__(self, cpuTime: Duration, wallTime: Duration):
        self.total_cpu_time_so_far: Duration = cpuTime
        self.total_wall_time_so_far: Duration = wallTime
