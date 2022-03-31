#!/usr/bin/env bash

rm -rf expected/*

create_screenings.py --screening-file details.json --extensions extensions.py --skeleton-file skeleton.inp --run-skeleton start_script.sh \
	--aux-file-dir aux-files/ --basename base --out-dir expected/
