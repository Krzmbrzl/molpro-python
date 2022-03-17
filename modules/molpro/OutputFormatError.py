from molpro import MolproError

class OutputFormatError(MolproError):
    """Exception thrown, if a provided Molpro output does not conform to the expected format"""
