#!/usr/bin/env python3

from typing import Optional
from typing import Dict
from typing import Any

import argparse
import json
from collections import OrderedDict
import os
import shutil
import importlib.util
import sys
import stat


class Extensions:
    @staticmethod
    def estimate_runtime(options: Dict[str, str]):
        return None

    @staticmethod
    def estimate_memory(options: Dict[str, str]):
        return None

    @staticmethod
    def estimate_disk_space(options: Dict[str, str]):
        return None

    @staticmethod
    def exclude(options: Dict[str, str]):
        return False


class ScreeningSet:
    def __init__(self, variable="", screenValues=[], screenNames=[]):
        self.variable = variable
        self.screenValues = screenValues
        self.screenNames = screenNames

        assert len(self.variable) > 0, "Variable name must not be empty!"
        assert len(self.variable) == len(self.variable.strip()
                                         ), "Variable name must not be trimmable"
        assert len(self.screenValues) == len(
            self.screenNames), "Amount of screen values and names differ!"


def getScreeningSets(json):
    sets = []

    for currentSet in json:
        screenValues = []
        screenNames = []
        for currentEntry in json[currentSet]:
            if type(currentEntry) == dict or type(currentEntry) == OrderedDict:
                # Entry given as object
                screenValues.append(currentEntry["value"])
                screenNames.append(currentEntry["name"])
            elif type(currentEntry) == str:
                # Entry given as simple string (assume name == value)
                screenValues.append(currentEntry)
                screenNames.append(currentEntry)
            else:
                raise RuntimeError("Set \"%s\" contains an entry of invalid type \"%s\" (expected list or str)" % (
                    currentSet, type(currentEntry)))

        sets.append(ScreeningSet(variable=currentSet,
                    screenValues=screenValues, screenNames=screenNames))

    return sets


def createFormatDicts(screeningSets):
    dicts = {}

    if len(screeningSets) == 0:
        return dicts

    counters = [0] * len(screeningSets)

    while counters[0] < len(screeningSets[0].screenValues):
        # Assemble respective format dict and the corresponding name
        name = ""
        formatDict = {}
        for i in range(len(counters)):
            name += screeningSets[i].screenNames[counters[i]] + "_"
            formatDict[screeningSets[i].variable] = screeningSets[i].screenValues[counters[i]]

        # Remove trailing '_'
        name = name[: -1]

        dicts[name] = formatDict

        # Increase counter(s)
        counters[-1] += 1
        for i in reversed(range(len(counters))):
            if i != 0 and counters[i] == len(screeningSets[i].screenValues):
                # This counter has reached its maximum, reset it and increase the following counter by one
                counters[i] = 0
                counters[i - 1] += 1
            else:
                break

    return dicts


def import_file(path: str, name: Optional[str] = None):
    if name is None:
        name = os.path.basename(path)
        if name.endswith(".py"):
            name = name[: -3]

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None:
        return None

    module = importlib.util.module_from_spec(spec)
    if module is None:
        return None

    sys.modules[name] = module

    if not spec.loader is None:
        spec.loader.exec_module(module)

    return module


def get_extensions(path: Optional[str]):
    extensions = Extensions()

    if not path is None:
        module = import_file(path, "screening.estimator")

        if not module is None:
            if hasattr(module, "estimate_runtime"):
                extensions.estimate_runtime = module.estimate_runtime
            if hasattr(module, "estimate_memory"):
                extensions.estimate_memory = module.estimate_memory
            if hasattr(module, "estimate_disk_space"):
                extensions.estimate_disk_space = module.estimate_disk_space
            if hasattr(module, "exclude"):
                extensions.exclude = module.exclude

    return extensions


def substitute(content: Optional[str], key: str, value: Any):
    if content is None:
        return None

    return content.replace("%" + key + "%", str(value))


def make_executable(path: str):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


def main():
    parser = argparse.ArgumentParser(
        description="This program creates the input files for performing a given screening")
    parser.add_argument("--screening-file", metavar="PATH",
                        help="The path to the file containing details on what to screen")
    parser.add_argument("--skeleton-file", metavar="PATH",
                        help="The path to the skeleton input file")
    parser.add_argument("--basename", metavar="NAME",
                        help="The base name of the generated files and folders", default="")
    parser.add_argument("--extensions", metavar="PATH",
                        help="The path to a Python file defining extension functions (e.g. for estimating resource requirements"
                        + " of a givencalculation)", default=None)
    parser.add_argument("--run-skeleton", metavar="PATH",
                        help="Path to a skeleton run-script. If the used estimator provides the necessary estimates, this skeleton file may"
                        + " use the placeholders %%runtime%%, %%memory%% and %%disk_space%% for the respective estimates", default=None)
    parser.add_argument("--aux-file-dir", metavar="PATH", help="The path to a dir containing aux. files that should be copied to all created dirs",
                        default=None)
    parser.add_argument("--out-dir", metavar="PATH", help="A path to the directory in which the respective files and directories shall be created",
                        default=".")
    parser.add_argument(
        "--file-extension", help="The file extension to use for the generated input file (including the period)", default=".inp")
    parser.add_argument("--start-script-name", metavar="NAME", help="The name of the generated start-script (if any)", default="start_script")

    args = parser.parse_args()

    # Get Python extensions (optional, user-supplied functions)
    extensions = get_extensions(args.extensions)

    # Parse the provided screening file (JSON)
    with open(args.screening_file, "r") as file:
        # Parse as JSON but make sure the relative order of entries is preserved (https://stackoverflow.com/a/23820416/3907364)
        parsedContents = json.load(file, object_pairs_hook=OrderedDict)

        screeningSets = getScreeningSets(parsedContents)

    # If provided, read in the skeleton definition for the run-script
    runSkeleton = None
    if not args.run_skeleton is None:
        with open(args.run_skeleton, "r") as file:
            runSkeleton = file.read()

    # Read and process the skeleton input file
    with open(args.skeleton_file, "r") as file:
        skeletonInput = file.read()

    # Create the outer product of all options that were provided in the screening file (all combinations of options)
    formatDicts = createFormatDicts(screeningSets)

    createdDirectories = []

    # Create a screening case for every of these combinations
    for currentName in formatDicts:
        # First check, whether the user explicitly wants to exclude this case
        if extensions.exclude(formatDicts[currentName]):
            continue

        formattedInput = skeletonInput
        scriptContent = runSkeleton
        for key in formatDicts[currentName]:
            formattedInput = substitute(
                formattedInput, key=key, value=formatDicts[currentName][key])
            scriptContent = substitute(
                scriptContent, key=key, value=formatDicts[currentName][key])

        # Get estimates for resource requirements via user extensions (may return None, if no estimator for this property is provided)
        estimatedRuntime = extensions.estimate_runtime(
            formatDicts[currentName])
        estimatedMemory = extensions.estimate_memory(
            formatDicts[currentName])
        estimatedDiskSpace = extensions.estimate_disk_space(
            formatDicts[currentName])

        if not estimatedRuntime is None:
            formattedInput = substitute(
                formattedInput, key="runtime", value=estimatedRuntime)
            scriptContent = substitute(
                scriptContent, key="runtime", value=estimatedRuntime)
        if not estimatedMemory is None:
            formattedInput = substitute(
                formattedInput, key="memory", value=estimatedMemory)
            scriptContent = substitute(
                scriptContent, key="memory", value=estimatedMemory)
        if not estimatedDiskSpace is None:
            formattedInput = substitute(
                formattedInput, key="disk_space", value=estimatedDiskSpace)
            scriptContent = substitute(
                scriptContent, key="disk_space", value=estimatedDiskSpace)

        if not args.basename == "":
            currentName = args.basename + "_" + currentName

        # Create a sub-dir for every screening case (note that we want this to fail, if the dir already exists)
        outDir = os.path.join(args.out_dir, currentName)
        os.mkdir(outDir)

        createdDirectories.append(currentName)

        inputName = currentName + args.file_extension

        # Write input file for calculation
        with open(os.path.join(outDir, inputName), "w") as outFile:
            # Write the actual output file
            assert formattedInput != None
            outFile.write(formattedInput)

        # Copy all auxiliary files into new subdir as well
        if not args.aux_file_dir is None:
            for currentFile in os.listdir(args.aux_file_dir):
                shutil.copy2(os.path.join(
                    args.aux_file_dir, currentFile), outDir)

        # Create a run-script and place it into the new directory
        if not scriptContent is None:
            scriptContent = substitute(
                scriptContent, key="input_file", value=inputName)
            assert scriptContent != None

            with open(os.path.join(outDir, args.start_script_name), "w") as file:
                file.write(scriptContent)

                file.flush()

                make_executable(file.name)

    # Generate a central start-script to procedurally execute all of the just generated screening cases
    masterScriptContent="#!/usr/bin/env bash\n\n"
    for currentDir in createdDirectories:
        masterScriptContent += "pushd \"" + currentDir + "\" > /dev/null\n"
        masterScriptContent += "./" + args.start_script_name + "\n"
        masterScriptContent += "popd > /dev/null\n"


    if not masterScriptContent == "":
        with open(os.path.join(args.out_dir, "start_screening.sh"), "w") as file:
            file.write(masterScriptContent)

            file.flush()

            make_executable(file.name)


if __name__ == "__main__":
    main()
