#!/usr/bin/env bash

memory=$(( %memory% * 8 )) # Convert from MegaWords to MegaBytes


qmolpro -n 1 -m ${memory}M -t %runtime%:00 -d %disk_space% %input_file%
