# File: kodbc_io.py
# Purpose: ODBC Interaction between dataframes and Kinetica.
# Author: Chad Juliano
# Date: 07/20/2018
###############################################################################

import pyodbc
import pandas as pd

# connection information
ODBC = 'DSN=KINETICA;UID=;PWD='


def get_odbc():
    """Convenience function to get a kinetica ODBC connection."""
    
    # autocommit=True must be enabled of this will break
    _cnxn = pyodbc.connect(ODBC, autocommit=True)
    _db_name = _cnxn.getinfo(pyodbc.SQL_DRIVER_NAME)
    _db_ver = _cnxn.getinfo(pyodbc.SQL_DBMS_VER)
    print('Connected to %s (%s)' % (_db_name, _db_ver))
    return _cnxn


def get_df(_sql):
    """Get a pandas dataframe from SQL."""
    
    _cnxn = get_odbc()
    _sql_df = pd.read_sql(_sql, _cnxn)
    _cnxn.close()
    return _sql_df


def get_row(_sql):
    """Execute a statement with a single row."""
    _cnxn = get_odbc()
    _cursor = _cnxn.execute(_sql)
    if(_cursor.rowcount == 0):
         raise Exception("Expected 1 row from statement and got none.")    
    _result = _cursor.fetchone()
    _cnxn.close()
    return _result
    

def execute(_sql):
    """Execute a statement and return the rowcount."""
    _cnxn = get_odbc()
    _rowcount = _cnxn.execute(_sql).rowcount
    _cnxn.close()
    return _rowcount

    
    