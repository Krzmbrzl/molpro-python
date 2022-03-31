from typing import Dict

def estimate_memory(options: Dict[str, str]):
    """Function to estimate the memory usage based on the given options"""

    # We estimate the memory usage based on the used basis set
    if options["basis"] == "cc-pVDZ":
        return 100
    elif options["basis"] == "cc-pVTZ":
        return 800
    elif options["basis"] == "cc-pVQZ":
        return 2000

    raise RuntimeError("Invalid basis encountered")


def estimate_runtime(options: Dict[str, str]):
    """Function to estimate the runtime based on the given options"""

    # We estimate the runtime usage based on the used basis set
    if options["basis"] == "cc-pVDZ":
        return 1
    elif options["basis"] == "cc-pVTZ":
        return 5
    elif options["basis"] == "cc-pVQZ":
        return 18

    raise RuntimeError("Invalid basis encountered")

def estimate_disk_space(options: Dict[str, str]):
    """Function to estimate the used/required disk space based on the given options"""

    # We estimate the disk space usage based on the used basis set
    if options["basis"] == "cc-pVDZ":
        return 7
    elif options["basis"] == "cc-pVTZ":
        return 50
    elif options["basis"] == "cc-pVQZ":
        return 200

    raise RuntimeError("Invalid basis encountered")

def exclude(options: Dict[str, str]):
    """Checks whether the given combination of options should be excluded from the screening"""

    if options["basis"] == "cc-pVQZ" and "mcscf" in options["scf_method"]:
        return True
    else:
        return False
