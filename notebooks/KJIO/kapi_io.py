# File: kapi_io.py
# Purpose: I/O of between dataframes and Kinetica with native API.
# Author: Chad Juliano
# Date: 07/20/2018
###############################################################################

import numpy as np
import pandas as pd
import gpudb
import sys

KDBC = gpudb.GPUdb(encoding='BINARY', host='127.0.0.1', port='9191')

KAPI_TYPE_MAP = { 'int64' :   gpudb.GPUdbRecordColumn._ColumnType.LONG,
                  'int32' :   gpudb.GPUdbRecordColumn._ColumnType.INT,
                  'int16' :   gpudb.GPUdbRecordColumn._ColumnType.INT,
                  'float64' : gpudb.GPUdbRecordColumn._ColumnType.DOUBLE,
                  'float32' : gpudb.GPUdbRecordColumn._ColumnType.FLOAT,
                  'object' :  gpudb.GPUdbRecordColumn._ColumnType.STRING }


def get_coldef(_col_name, _np_dtype, _col_props):
    """Convert a Numpy type to Kinetica type."""
    
    if(str(_np_dtype) not in KAPI_TYPE_MAP):
        raise Exception('Type not supported: {}'.format(_np_dtype))
        
    _k_type = KAPI_TYPE_MAP[str(_np_dtype)]
    _k_properties = []
    
    if(_col_name in _col_props):
        _k_properties = _col_props[_col_name]
        
    if(_k_type == gpudb.GPUdbRecordColumn._ColumnType.STRING and len(_k_properties) == 0):
        _k_properties.append(gpudb.GPUdbColumnProperty.CHAR16)
             
    return gpudb.GPUdbRecordColumn(_col_name, _k_type, _k_properties)

      
def save_df(_df, _table_name, _schema, _kdbc=KDBC, _col_props={}):
    """Save a Dataframe to a Kinetica table."""
    
    # Should index be used to create a column?
    _use_index = (_df.index.name != None)
    
    # Construct the type to use for creating the table.
    _result_type = []
    
    if(_use_index):
        _idx_type = get_coldef(_df.index.name, _df.index.dtype, _col_props)
        _idx_type.column_properties.append('shard_key')
        _result_type.append(_idx_type)
        
    for _idx in range(_df.columns.size):
        _col_name = _df.columns[_idx]
        _dtype = _df.dtypes[_idx]
        _result_type.append(get_coldef(_col_name, _dtype, _col_props))
        
    print('Dropping table: <{}>'.format(_table_name))
    _kdbc.clear_table(_table_name, options={ 'no_error_if_not_exists':'true' })
    
    print('Creating table: <{}>'.format(_table_name))
    for _idx, _coldef in enumerate(_result_type):
        print('Column {}: <{}> ({}) {}'.format(_idx, _coldef.name, _coldef.column_type, _coldef.column_properties))
    
    _is_replicated = 'false'
    _type_obj = gpudb.GPUdbRecordType(columns=_result_type, label=_table_name)
    _result_table = gpudb.GPUdbTable(db=_kdbc, _type=_type_obj, name=_table_name,
        options={'collection_name': _schema,
                 'is_replicated': _is_replicated} )

    # Convert to records so we can preserve the column dtypes
    _insert_records = _df.to_records(index=_use_index)
    
    # Call item() so the types are converted to python native types
    _insert_rows = [ list(x.item()) for x in _insert_records ]

    if(len(_insert_rows) > 0):
        _result_table.insert_records(_insert_rows)
    
    print('Inserted rows into <{}.{}>: {}'.format(_schema, _table_name, len(_insert_rows)))


def load_df(_input_table, _kdbc=KDBC):
    """Load a dataframe from a Kinetica table."""
    
    BATCH_SIZE=10000
    _offset = 0
    _table_df = pd.DataFrame()
    
    #print('Getting records from <{}>'.format(_input_table), end='', flush=True)
    sys.stdout.write('Getting records from <{}>'.format(_input_table))
    while True:
        _response = _kdbc.get_records(table_name=_input_table,
                                    offset=_offset, limit=BATCH_SIZE)
        check_response(_response)
        
        res_decoded = gpudb.GPUdbRecord.decode_binary_data(
            _response['type_schema'], 
            _response['records_binary'])
        
        # print something to show we are working
        #print('.', end='', flush=True)
        sys.stdout.write('.')
        
        _offset += len(res_decoded)
        _table_df = _table_df.append(res_decoded)
        if _response['has_more_records'] == False:
            break;
            
    print('')
    print('Records Retrieved: {}'.format(_table_df.shape))
    return _table_df


def check_response(_response):
    _status = _response['status_info']['status']
    
    if(_status != 'OK'):
        _message = _response['status_info']['message']
        raise Exception('[%s]: %s' % (_status, _message))

    return _response

