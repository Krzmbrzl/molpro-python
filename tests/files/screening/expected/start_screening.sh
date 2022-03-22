#!/usr/bin/env bash

pushd "cc-pVDZ_first_rhf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVDZ_first_mcscf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVDZ_second_rhf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVDZ_second_mcscf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVTZ_first_rhf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVTZ_first_mcscf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVTZ_second_rhf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVTZ_second_mcscf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVQZ_first_rhf" > /dev/null
./start_script
popd > /dev/null
pushd "cc-pVQZ_second_rhf" > /dev/null
./start_script
popd > /dev/null
