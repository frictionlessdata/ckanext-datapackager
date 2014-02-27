'''Unit tests for lib/csv.py.

'''
import os.path

import ckanext.b2.lib.csv as lib_csv


def test_infer_schema_from_csv_file():
    '''Test that infer_schema_from_csv_file infers the correct schema from a
    sample CSV file.

    This should be broken up into different tests for different types of CSV
    file. For now we just have this.

    '''
    # Get the absolute path to the test data file.
    path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
    path = os.path.join(os.path.split(__file__)[0], path)
    abspath = os.path.abspath(path)

    schema = lib_csv.infer_schema_from_csv_file(abspath)

    assert schema == {
        'fields': [
            {'name': 'playerID', 'type': 'string', 'index': 0},
            {'name': 'yearID', 'type': 'integer', 'index': 1},
            {'name': 'gameNum', 'type': 'number', 'index': 2},
            {'name': 'gameID', 'type': 'string', 'index': 3},
            {'name': 'teamID', 'type': 'string', 'index': 4},
            {'name': 'lgID', 'type': 'string', 'index': 5},
            {'name': 'GP', 'type': 'number', 'index': 6},
            {'name': 'startingPos', 'type': 'number', 'index': 7},
        ]
    }


def test_infer_schema_from_another_csv_file():
    '''Another sample CSV file test.'''
    path = '../test-data/test.csv'
    path = os.path.join(os.path.split(__file__)[0], path)
    abspath = os.path.abspath(path)

    schema = lib_csv.infer_schema_from_csv_file(abspath)

    assert schema == {
        'fields': [
            {'name': 'datetime', 'type': 'string', 'index': 0},
            {'name': 'timedelta', 'type': 'string', 'index': 1},
            {'name': 'integer', 'type': 'integer', 'index': 2},
            {'name': 'number', 'type': 'number', 'index': 3},
            {'name': 'boolean', 'type': 'boolean', 'index': 4},
            {'name': 'object', 'type': 'string', 'index': 5},
        ]
    }
