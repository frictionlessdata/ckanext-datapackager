'''Some library functions for dealing with CSV files.

These are meant to be reusable library functions not tied to CKAN, so they
shouldn't know anything about CKAN.

'''
import StringIO

import pandas
import numpy


def _dtype_to_json_table_schema_type(dtype):
    '''Convert a pandas dtype object into a JSON Table Schema type string.

    '''
    if dtype == numpy.datetime64:
        return 'datetime'
    elif dtype == numpy.timedelta64:
        # JSON Table Schema doesn't support deltas.
        return 'any'
    elif dtype == numpy.int64:
        return 'integer'
    elif dtype == numpy.float64:
        return 'number'
    elif dtype == numpy.bool:
        return 'boolean'
    elif dtype == numpy.object:
        return 'string'
    else:
        return 'any'


def infer_schema_from_csv_file(path):
    '''Return a JSON Table Schema for the given CSV file.

    This will guess the column titles (e.g. from the file's header row) and
    guess the types of the columns.

    '''
    # Read the first 1024 bytes of the file into a pandas dataframe.
    dataframe = pandas.read_csv(StringIO.StringIO(open(path).read(1024)))

    fields = []
    for column in dataframe.columns:
        fields.append({
            "name": column,
            "type": _dtype_to_json_table_schema_type(dataframe[column].dtype)
        })

    schema = {
        "fields": fields,
        # "primaryKey': TODO,
    }

    return schema
