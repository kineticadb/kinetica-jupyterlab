# File: kapi_io.py
# Purpose: UDF execution helper functions.
# Author: Chad Juliano
# Date: 07/20/2018
###############################################################################

import os
import time
import sys
import kapi_io


def submit_proc(_proc_name, _input_table_names, _output_table_names, _params={}, _kdbc=kapi_io.KDBC):
    """Submit a python script as a UDF and wait for response."""
    
    _run_id = execute_proc(_proc_name=_proc_name, 
                           _input_table_names=_input_table_names, 
                           _output_table_names=_output_table_names,
                           _params=_params,
                           _kdbc=_kdbc)
    
    _result = monitor_proc(_run_id, _kdbc=_kdbc)
    
    return _result

    
def create_proc(_proc_name, _file_paths, _execution_mode='distributed', _kdbc=kapi_io.KDBC):
    """Create a UDF from a python script."""
    _file_bytes = {}
    for _script_path in _file_paths:
        _script_name = os.path.basename(_script_path)
        print('Reading file: {}'.format(_script_name))
        with open(_script_path, 'rb') as _fp:
            _file_bytes[_script_name] = _fp.read()
    
    print('Creating UDF: {} [{}]'.format(_proc_name, ', '.join(_file_paths)))
    _response = _kdbc.has_proc(proc_name = _proc_name)
    kapi_io.check_response(_response)

    ## Drop older version of proc with same name if it already exists
    if _response['proc_exists']:
        print('Dropping older version of proc: %s ' % (_proc_name))
        _kdbc.delete_proc(proc_name = _proc_name)
        kapi_io.check_response(_response)

    response = _kdbc.create_proc(
        proc_name=_proc_name,
        execution_mode=_execution_mode,
        files=_file_bytes,
        command='python',
        args=[ os.path.basename(_file_paths[0] ) ],
        options={})
    kapi_io.check_response(_response)

    
def execute_proc(_proc_name, _input_table_names, _output_table_names, _params={}, _kdbc=kapi_io.KDBC):
    """Execute a UDF"""
    
    _response = _kdbc.execute_proc(
        proc_name=_proc_name,
        params=_params,
        bin_params={},
        input_table_names=_input_table_names,
        input_column_names={},
        output_table_names=_output_table_names,
        options={} )
    kapi_io.check_response(_response)

    _run_id = _response['run_id']

    print('Starting UDF: %s (id=%s)' % (_proc_name, _run_id))
    print('   Input Tables: %s' % (_input_table_names))
    print('   Output Tables: %s' % (_output_table_names))
    print
    return _run_id


def monitor_proc(_run_id , _kdbc=kapi_io.KDBC):
    """Wait until a UDF completes and print the status."""
    
    _overall_statuses = None
    _start_time = time.time()

    while True:
        _response = _kdbc.show_proc_status(run_id=_run_id)
        kapi_io.check_response(_response)
        
        _statuses = _response['statuses'][_run_id]
        _status_list = list(_statuses.values())
        _completed = _status_list.count('complete')
        _total = len(_status_list)
        _time = time.time() - _start_time

        print('[%s] UDF Running... (%d/%d complete) (time=%.1f)' % (_run_id, _completed, _total, _time))
        sys.stdout.flush()

        _overall_statuses = _response['overall_statuses'][_run_id]
        if(_overall_statuses != 'running'):
            break;

        time.sleep(5)

    print('[%s] UDF finished with status: %s ' % (_run_id, _overall_statuses))
    _results = udf_report_summary(_response, _run_id)

    if _overall_statuses != 'complete':
        raise Exception('final proc state is: %s' % (_overall_statuses))
        
    return _results


def udf_report_summary(_response, _run_id):
    """Summarize the status of a completed UDF."""
    
    _statuses = _response['statuses'][_run_id]
    _messages = _response['messages'][_run_id]
    _results = _response['results'][_run_id]
    _timings = _response['timings'][_run_id]

    for _tom in sorted(_statuses):
        _status = _statuses[_tom]
        _message = _messages[_tom]
        _result = _results[_tom]

        _total_str = ''
        _total_ms = _timings[_tom].get('total')
        if(_total_ms != None):
            _total_sec = float(_total_ms) / 1000.0
            _total_str = '(time=%.1f sec)' % _total_sec

        print('TOM %s: [%s] %s %s %s' % (_tom, _status, _result, _message, _total_str))
        
    return _results

    
def read_file(_file_path):
    _bytes = b''
    _file = open(_file_path, 'rb')

    while True:
        _chunk = _file.read(1024)
        if not _chunk:
            break
        _bytes = _bytes + _chunk

    _file.close()
    return _bytes
