#!/usr/bin/env bash

memory=$(( %memory% * 8 )) # Convert from MegaWords to MegaBytes


# All parameters can be accessed here as well
echo "Submitting job that uses the following correlation method: %correlation_method%"

qmolpro -n 1 -m ${memory}M -t %runtime%:00 -d %disk_space% %input_file%
