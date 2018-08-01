#! /usr/bin/env bash
# Script: gpudb-docker.sh
# Purpose: Docker run script.
###############################################################################

set -o nounset    # give error for any unset variables
set -o errexit    # exit if a command returns non-zero status

./start-gpudb.sh
./start-jupyter.sh

# send log output to console
tail -F /opt/gpudb/core/logs/gpudb.log
