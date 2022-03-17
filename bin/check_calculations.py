#!/usr/bin/env python3

import argparse
import os
from enum import Enum

from molpro import OutputFileParser

class State(Enum):
    OK = 1
    PENDING = 2
    ERROR = 3


def processFile(path):
    parser = OutputFileParser()

    output = parser.parse(path, parse_details=False)

    if len(output.errors) > 0:
        return State.ERROR

    return State.OK if output.calculation_finished else State.PENDING

def printStatus(path: str, state: State, indent: str = ""):
    msg = indent
    if state == State.OK:
        msg += "\033[32m" + "OK" + "\033[0m"
    elif state == State.PENDING:
        msg += "PENDING"
    elif state == State.ERROR:
        msg += "\033[31m" + "ERROR" + "\033[0m"

    msg += ": " + path

    print(msg)


def main():
    parser = argparse.ArgumentParser(description="Evaluates and prints the status of (Molpro) calculations in the given directory")

    parser.add_argument("paths", help="A list of paths (space-separated) to output files or directories containing output files", nargs="*")

    args = parser.parse_args()

    for currentPath in args.paths:
        if os.path.isdir(currentPath):
            print(currentPath + ":")
            for subFile in os.listdir(currentPath):
                fullPath = os.path.join(currentPath, subFile)

                if os.path.isfile(fullPath) and fullPath.endswith(".out") and not subFile.startswith("slurm"):
                    printStatus(fullPath, processFile(fullPath), indent="  > ")
        else:
            printStatus(currentPath, processFile(currentPath))


if __name__ == "__main__":
    main()
