#!/usr/bin/env python3

from typing import Optional
from typing import Dict
from typing import Any
from typing import List
from typing import Tuple

import argparse
import json
from collections import OrderedDict
import os
import shutil
import importlib.util
import sys
import stat
import logging

from screening import Extensions
from screening import utils

logger = logging.getLogger("screening.main")


def getScreeningSets(json: Any) -> Tuple[List[Dict[str, Any]], List[List[str]]]:
    combinedSubstitutions = []
    combinedNames = []
    for currentKey in json:
        currentSubstitutions = []
        currentNames = []
        for currentEntry in json[currentKey]:
            if type(currentEntry) == dict or type(currentEntry) == OrderedDict:
                paramSubstitutions = []
                paramNames = []
                if "parameter" in currentEntry:
                    paramSubstitutions, paramNames = getScreeningSets(
                        currentEntry["parameter"])

                # Entry given as object
                substitutions = dict()
                substitutions[currentKey] = currentEntry["value"]
                names = [[currentEntry["name"]]]

                # Combine with parameter set
                substitutions = utils.combine(
                    [substitutions], paramSubstitutions)
                names = utils.combine(names, paramNames)
            elif type(currentEntry) == str:
                # Entry given as simple string (assume name == value)
                substitutions = [dict()]
                substitutions[0][currentKey] = currentEntry
                names = [[currentEntry]]
            else:
                raise RuntimeError("Set \"%s\" contains an entry of invalid type \"%s\" (expected list or str)" % (
                    currentKey, type(currentEntry)))

            assert len(substitutions) == len(names)
            currentSubstitutions += substitutions
            currentNames += names

        combinedSubstitutions = utils.combine(
            combinedSubstitutions, currentSubstitutions)
        combinedNames = utils.combine(combinedNames, currentNames)

    return combinedSubstitutions, combinedNames


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
    parser.add_argument("--start-script-name", metavar="NAME",
                        help="The name of the generated start-script (if any)", default="start_script")
    parser.add_argument("--extend", help="A flag indicating that the current run should extend an existing screening set, meaning that only those "
                        + "cases are created that don't exist yet", action="store_true", default=False)

    args = parser.parse_args()

    # Get Python extensions (optional, user-supplied functions)
    extensions = get_extensions(args.extensions)

    # Parse the provided screening file (JSON)
    with open(args.screening_file, "r") as file:
        # Parse as JSON but make sure the relative order of entries is preserved (https://stackoverflow.com/a/23820416/3907364)
        parsedContents = json.load(file, object_pairs_hook=OrderedDict)

        substitutions, names = getScreeningSets(parsedContents)
        assert len(substitutions) == len(names)

    # If provided, read in the skeleton definition for the run-script
    runSkeleton = None
    if not args.run_skeleton is None:
        with open(args.run_skeleton, "r") as file:
            runSkeleton = file.read()

    # Read and process the skeleton input file
    with open(args.skeleton_file, "r") as file:
        skeletonInput = file.read()

    createdDirectories = []

    for i in range(len(names)):
        currentName = "_".join(names[i])
        currentSubstitutions = substitutions[i]
        if not args.basename == "":
            currentName = args.basename + "_" + currentName
        inputName = currentName + args.file_extension

        utils.add_extra_substitutions(
            currentSubstitutions, extensions=extensions, extra={"input_file": inputName})

        if extensions.exclude(currentSubstitutions):
            continue

        formattedInput = skeletonInput
        scriptContent = runSkeleton
        formattedInput = utils.format(formattedInput, currentSubstitutions)
        if not scriptContent is None:
            scriptContent = utils.format(scriptContent, currentSubstitutions)

        # Create a sub-dir for the current screening case
        outDir = os.path.join(args.out_dir, currentName)
        if os.path.exists(outDir):
            if args.extend:
                # This case apparently already exists
                continue
            else:
                # If we're not in extend-mode, then encountering an already existing case is considered an error
                logger.error(
                    "Directory for screening case \"%s\" already exists" % outDir)
                return 1
        os.mkdir(outDir)

        createdDirectories.append(currentName)

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
            with open(os.path.join(outDir, args.start_script_name), "w") as file:
                file.write(scriptContent)

                file.flush()

                make_executable(file.name)

    # Generate a central start-script to procedurally execute all of the just generated screening cases
    masterScriptContent = "#!/usr/bin/env bash\n\n"
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
