#!/usr/bin/env python3

import argparse
import os
from enum import Enum

from molpro import OutputFileParser
from molpro import MolproError

class State(Enum):
    OK = 1
    PENDING = 2
    ERROR = 3
    WARNING = 4
    INVALID = 5

# https://stackoverflow.com/a/27265453
NO_COLOR = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
ORANGE = "\033[33m"
BLUE = "\033[34m"
PURPLE = "\033[35m"

def processFile(path):
    parser = OutputFileParser()

    try:
        output = parser.parse(path, parse_details=False)

        if len(output.errors) > 0:
            return State.ERROR
        if len(output.warnings) > 0:
            return State.WARNING

        return State.OK if output.calculation_finished else State.PENDING
    except MolproError:
        return State.INVALID


def printStatus(path: str, state: State, indent: str = ""):
    msg = indent
    if state == State.OK:
        msg += GREEN + "OK" + NO_COLOR
    elif state == State.PENDING:
        msg += BLUE + "PENDING" + NO_COLOR
    elif state == State.ERROR:
        msg += RED + "ERROR" + NO_COLOR
    elif state == State.WARNING:
        msg += ORANGE + "WARNING" + NO_COLOR
    elif state == State.INVALID:
        msg += PURPLE + "INALID" + NO_COLOR

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
