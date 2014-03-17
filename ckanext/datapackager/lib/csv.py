'''Some library functions for dealing with CSV files.

These are meant to be reusable library functions not tied to CKAN, so they
shouldn't know anything about CKAN.

'''
import pandas
import numpy


def _dtype_to_json_table_schema_type(dtype):
    '''Convert a pandas dtype object into a JSON Table Schema type string.

    '''
    if dtype == numpy.int64:
        return 'integer'
    elif dtype == numpy.float64:
        return 'number'
    elif dtype == numpy.bool:
        return 'boolean'
    else:
        return 'string'


def infer_schema_from_csv_file(path):
    '''Return a JSON Table Schema for the given CSV file.

    This will guess the column titles (e.g. from the file's header row) and
    guess the types of the columns.

    '''
    dataframe = pandas.read_csv(path)
    description = dataframe.describe()  # Summary stats about the columns.

    fields = []
    for (index, column) in enumerate(dataframe.columns):

        field = {
            "index": index,
            "name": column,
            "type": _dtype_to_json_table_schema_type(dataframe[column].dtype),
        }

        # Add some descriptive statistics about the column to the field dict.
        column_description = description.get(column)
        if column_description is not None:
            for key in column_description.keys():
                field[key] = column_description[key]

        fields.append(field)

    schema = {
        "fields": fields,
        # "primaryKey': TODO,
    }

    return schema
