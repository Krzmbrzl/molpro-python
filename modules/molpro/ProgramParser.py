program_parsers = {}

def register_program_parser(cls):
    program_parsers[cls.__name__.lower()] = cls
    return cls

