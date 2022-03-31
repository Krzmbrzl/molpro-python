from typing import Dict

class Extensions:
    """A class describing an interface for functions that can be implemented in a separate file
    to be passed to the screening script. The default implementations here are used, if no such file
    is provided (or is missing some of these implementations)"""

    @staticmethod
    def estimate_runtime(options: Dict[str, str]):
        del options
        return None

    @staticmethod
    def estimate_memory(options: Dict[str, str]):
        del options
        return None

    @staticmethod
    def estimate_disk_space(options: Dict[str, str]):
        del options
        return None

    @staticmethod
    def exclude(options: Dict[str, str]):
        del options
        return False

