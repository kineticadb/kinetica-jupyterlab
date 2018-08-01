# File: gpudb_df.py
# Purpose: Utilities for dataframe conversion
###############################################################################

import pandas as pd
import numpy as np
import gpudb
import pyodbc

KDBC = gpudb.GPUdb(encoding='BINARY', host="127.0.0.1", port="9191")
SCHEMA = 'PHARMACY'
ODBC = 'DSN=KINETICA;UID=;PWD='

def load_df(_input_table):
    BATCH_SIZE=10000
    _offset = 0
    _table_df = pd.DataFrame()
    
    print('Getting records from <{}>'.format(_input_table), end='', flush=True)
    
    while True:
        _response = KDBC.get_records(table_name=_input_table,
                                    offset=_offset,
                                    limit=BATCH_SIZE)
        
        res_decoded = gpudb.GPUdbRecord.decode_binary_data(
            _response["type_schema"], 
            _response["records_binary"])
        
        _retrieved_records = len(res_decoded)
        _offset += _retrieved_records
        #print('Got records: {}/{}'.format(_retrieved_records, _offset))
        print('.', end='', flush=True)
        
        _table_df = _table_df.append(res_decoded)
        
        if _response['has_more_records'] == False:
            break;
            
    print('')
    print('Records Retrieved: {}'.format(_table_df.shape))
    return _table_df


def get_coldef(_col_name, _np_dtype):
    if(_np_dtype == np.int64):
        return [_col_name, gpudb.GPUdbRecordColumn._ColumnType.LONG]
    elif(_np_dtype == np.int32):
        return [_col_name, gpudb.GPUdbRecordColumn._ColumnType.INT]
    elif(_np_dtype == np.float64):
        return [_col_name, gpudb.GPUdbRecordColumn._ColumnType.DOUBLE]
    elif(_np_dtype == np.float32):
        return [_col_name, gpudb.GPUdbRecordColumn._ColumnType.FLOAT]
    elif(_np_dtype == np.object):
        return [_col_name, gpudb.GPUdbRecordColumn._ColumnType.STRING, gpudb.GPUdbColumnProperty.CHAR16]
    else:
        raise Exception('Type not supported: {}'.format(_np_dtype))

        
def save_df(_df, _res_table, _schema=SCHEMA):
    print('Dropping table: <{}>'.format(_res_table))
    KDBC.clear_table(_res_table, options={ 'no_error_if_not_exists':'true' })
    
    # Should index be used to create a column?
    _use_index = (_df.index.name != None)
    
    # Construct the type to use for creating the table.
    _result_type = []
    
    if(_use_index):
        _result_type.append(get_coldef(_df.index.name, _df.index.dtype))
        
    for _idx in range(_df.columns.size):
        _col_name = _df.columns[_idx]
        _dtype = _df.dtypes[_idx]
        _result_type.append(get_coldef(_col_name, _dtype))
        
    print('Creating table: <{}>'.format(_res_table))
    for _idx, _coldef in enumerate(_result_type):
        print('Column {}: <{}> ({})'.format(_idx, _coldef[0], _coldef[1]))
    
    # This function only supports replicated tables.
    _result_table = gpudb.GPUdbTable(db=KDBC, _type=_result_type, name=_res_table,
        options={'collection_name': _schema,
                 'is_replicated': 'true'} )

    # Convert to records so we can preserve the column dtypes
    _insert_records = _df.to_records(index=_use_index)
    
    # Call item() so the types are converted to python native types
    _insert_rows = [ list(x.item()) for x in _insert_records ]

    _result_table.insert_records(_insert_rows)
    print('Inserted rows into <{}.{}>: {}'.format(_schema, _res_table, len(_insert_rows)))
    

def get_odbc():
    _cnxn = pyodbc.connect(ODBC, autocommit=True)
    _db_name = _cnxn.getinfo(pyodbc.SQL_DRIVER_NAME)
    _db_ver = _cnxn.getinfo(pyodbc.SQL_DBMS_VER)
    print('Connected to %s (%s)' % (_db_name, _db_ver))
    return _cnxn
