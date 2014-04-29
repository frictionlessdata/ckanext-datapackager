'''Some library functions for dealing with CSV files.

These are meant to be reusable library functions not tied to CKAN, so they
shouldn't know anything about CKAN.

'''
import datetime
import cStringIO

import pandas
import numpy
import dateutil
import magic
import ckanext.datapackager.lib.tzinfos as tzinfos

import ckan.lib.helpers as helpers


def _dtype_to_json_table_schema_type(dtype):
    '''Convert a pandas dtype object into a JSON Table Schema type string.

    '''
    if dtype == numpy.int64:
        return 'integer'
    elif dtype == numpy.float64:
        return 'number'
    elif dtype == numpy.bool:
        return 'boolean'
    elif dtype.type == numpy.datetime64:
        return 'datetime'
    else:
        return 'string'


def infer_schema_from_csv_file(path):
    '''Return a JSON Table Schema for the given CSV file.

    This will guess the column titles (e.g. from the file's header row) and
    guess the types of the columns.

    '''
    buffer = open(path).read()
    dataframe = pandas.read_csv(cStringIO.StringIO(buffer), sep=None)

    # reparse the dataframe with columns as dates if their type is a json object
    objects = [col for col, type in
               zip(dataframe.columns, dataframe.dtypes)
               if type.name == 'object']
    dataframe = pandas.read_csv(cStringIO.StringIO(buffer), sep=None,
                                parse_dates=objects)

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

        for key, value in field.items():
            if isinstance(value, numpy.bool_):
                # Numpy's booleans are not serializable.
                if value:
                    field[key] = True
                else:
                    field[key] = False

        if field['type'] == 'datetime':
            try:
                field['temporal_extent'] = temporal_extent(
                    cStringIO.StringIO(buffer), index)
            except (ValueError, TypeError, IOError, IndexError):
                pass

        fields.append(field)

    schema = {
        "fields": fields,
        # "primaryKey': TODO,
    }

    return schema


def _parse(datestring):
    '''Parse a string and return a datetime.

    This is passed to pandas as a custom date string parser function.

    This is a wrapper for dateutil.parser.parse(), the same date string parser
    that pandas uses by default, but we customize the options that get passed
    to it because pandas seems to tell it to ignore timezones in the date
    strings.

    '''
    return dateutil.parser.parse(datestring, ignoretz=False, tzinfos=tzinfos.tzinfos,
                                 default=datetime.datetime(1, 1, 1, 0, 0, 0))


def temporal_extent(path, column_num):
    '''Return the temporal extent of the given column in the given CSV file.

    Lots of different date formats are understood
    (uses dateutil.parser.parse(), via pandas).

    The dates in the returned time interval will have timezones if the dates in
    the input data have timezones.

    :param path: a CSV file or the path to a CSV file
    :type path: file-like object or string

    :param column_num: which column in the CSV file to process (the first
        column is 0)
    :type column_num: int

    :returns: An ISO 8601 time interval in the format START_DATE/END_DATE,
    for example "2014-02-26T:21:22:45/2015-04-26T:20:19:32".
    :rtype: string

    :raises ValueError: if the input data contains values that can't be parsed
                        as dates.

    :raises ValueError: if column_num is not an int

    :raises TypeError: if the input contains both offset-naive
                       (without a timezone or UTC offset) and offset-aware
                       (with a timezone or offset) datetimes

    :raises IOError: if the given path cannot be read as a CSV file

    :raises IndexError: if the given column is invalid or does not exist in
                        the CSV file

    '''
    dataframe = pandas.read_csv(path, parse_dates=[column_num],
                                date_parser=_parse)

    return _calculate_temporal_extent(dataframe, column_num)


def _calculate_temporal_extent(dataframe, column_num):
    column_title = dataframe.columns[column_num]
    time_series = dataframe[column_title]
    extent = '{min}/{max}'.format(min=time_series.min().isoformat(),
                                    max=time_series.max().isoformat())

    return extent


def resource_is_csv_file(path):
    csv_types = ['text/plain','text/csv','text/tsv',
                 'text/comma-seperated-values']
    file_type = magic.from_file(path)
    return file_type in csv_types
