#! /usr/bin/env bash
# Script: gpudb-docker.sh
# Purpose: Start gpudb
###############################################################################

set -o nounset    # give error for any unset variables
set -o errexit    # exit if a command returns non-zero status

# import configuration functions
_script_dir=$(cd $(dirname $0); pwd -P)
source $_script_dir/lib_config_functions.sh

################################
# Update gpudb.conf

#_gpudb_conf=/opt/gpudb/core/etc/gpudb.conf
#cp --verbose $_gpudb_conf ${_gpudb_conf}.${_timestamp}

#replace_conf_param $_gpudb_conf 'enable_procs' 'true'
#replace_conf_param $_gpudb_conf 'enable_worker_http_servers' 'true'
#replace_conf_param $_gpudb_conf 'persist_directory' '/opt/share'

# merge gpudb.conf properties
/opt/gpudb/core/bin/gpudb_config_compare.py \
   /opt/share/conf/gpudb.conf \
   /opt/gpudb/core/etc/gpudb.conf.template \
   /opt/gpudb/core/etc/gpudb.conf

################################
# Update gaia.properties

_gaia_props=/opt/gpudb/tomcat/webapps/gadmin/WEB-INF/classes/gaia.properties
replace_conf_param $_gaia_props 'require_strong_password' 'false'

################################
# Start gpudb

# Clear any previous logs
:> /opt/gpudb/core/logs/gpudb.log

echo "INIT: Starting host manager..."
if ! /etc/init.d/gpudb_host_manager start
then
    cat /opt/gpudb/core/logs/gpudb.log
    echo "ERROR: Failed to start the host manager. Check the above log messages."
    exit 1
fi

if [ "$FULL_START" -ne 1 ]
then
    echo "INIT: Not starting gpudb. (FULL_START != 1)"
    exit 0
fi

# try to start the DB. This will fail if the license key is not valid.
echo "INIT: Starting gpudb..."
if ! /etc/init.d/gpudb start
then
    echo "ERROR: gpudb failed to start. Is your license key valid?"
    echo "INFO: Try setting FULL_START=0 in docker-compose.yml and login to GAdmin"
    exit 1
fi
