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
            {'name': 'playerID', 'type': 'string'},
            {'name': 'yearID', 'type': 'integer'},
            {'name': 'gameNum', 'type': 'number'},
            {'name': 'gameID', 'type': 'string'},
            {'name': 'teamID', 'type': 'string'},
            {'name': 'lgID', 'type': 'string'},
            {'name': 'GP', 'type': 'number'},
            {'name': 'startingPos', 'type': 'number'},
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
            {'name': 'datetime', 'type': 'string'},
            {'name': 'timedelta', 'type': 'string'},
            {'name': 'integer', 'type': 'integer'},
            {'name': 'number', 'type': 'number'},
            {'name': 'boolean', 'type': 'boolean'},
            {'name': 'object', 'type': 'string'},
        ]
    }
