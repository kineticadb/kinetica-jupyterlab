# Script: lib_config_functions.sh
# Purpose: Utility functions for updating configurations.
# Maintainer: Chad Juliano
# Date: 01/15/2018
###############################################################################

set -o nounset    # give error for any unset variables
set -o errexit    # exit if a command returns non-zero status
set -o errtrace   # make errexit apply to functions too

# Log a fatal message and terminate the program.

function fn_die {
     >&2 echo "ERROR: $@"
    exit 1
}

# install error handler. This will invoke the error handling function
# If the script terminates due to CTRL-C, kill, or an error.

function fn_handle_error {
    local err_line=$((BASH_LINENO[0]))
    local err_func=${FUNCNAME[1]}
    fn_die "at '${BASH_COMMAND}' (${err_func}:${err_line}) "
}
trap "fn_handle_error" INT TERM ERR


function fn_sed_sub {
  local _file="$1"
  local _address="$2"
  local _replace="$3"
  local _append="${4-}"

  echo "Updating ${_file}: ${_param} = $(eval echo ${_value})"

  # This sed command is designed to reuturn 1 if no substitutions were made.
  # It does this by
  # 1) using 'h' commmand to save the result from the pattern-space (PS) to the hold-space (HS)
  # 2) at the last line use 'x' to swap PS and HS.
  # 3) if HS is not empty then exit with 'q0'
  # 4) otherwise exit with 'q1'
  #
  local _result=0
  sed -i "/${_address}/ {s${_replace};h}; \${x; /./{x;q0}; x; q1}" $_file || _result=$?

  if [ $_result -gt 0 ]; then
    if [ -z "$_append" ]; then
      fn_die "Could not find param <$_param> in $_file."
    fi
    echo "Append ${_file}: ${_append}"
    echo "$_append" >> $_file
  fi
}


function replace_conf_param {
  local _file="$1"
  local _param="$2"
  local _value="$3"
  local _append="${4-}"

  if [ "$_append" == "true" ]; then
    _append="${_param} = ${_value}"
  fi

  # escape slashes
  _value="${_value////\\/}"

  fn_sed_sub $_file "^${_param}[[:space:]]*=" "/=.*/= ${_value}/" "$_append"
}


function replace_httpd_param {
  local _file="$1"
  local _param="$2"
  local _value="$3"

  # escape slashes
  _value="${_value////\\/}"

  fn_sed_sub $_file "\(#[[:space:]]*\)\?${_param}.*" "//${_param} ${_value}/"
}

# declarations
_gpudb=/opt/gpudb/core/bin/gpudb
_timestamp=$(date +%Y%m%d_%H%M%S)
_cert_dir=/opt/gpudb/certs
_server_cert=${_cert_dir}/kinetica_server_cert.pem
_server_key=${_cert_dir}/kinetica_server_key.pem
_root_jks=${_cert_dir}/kinetica_rootca.jks
_root_cert=${_cert_dir}/kinetica_rootca_cert.pem


# confirm gpudb is stopped
if $_gpudb gpudb-status; then
  fn_die "Gpudb must not be running"
fi

# confirm gpudb is stopped
if $_gpudb host-manager-status; then
  fn_die "Host manager must not be running"
fi
