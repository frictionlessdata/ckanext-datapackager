'''Unit tests for lib/csv.py.

'''
import os.path

import ckanext.datapackager.lib.csv as lib_csv


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
            {'index': 0, 'name': 'playerID', 'type': 'string'},
            {'25%': 1957.0,
             '50%': 1975.0,
             '75%': 1996.0,
             'count': 4912.0,
             'index': 1,
             'max': 2013.0,
             'mean': 1975.2168159609121,
             'min': 1933.0,
             'name': 'yearID',
             'std': 23.055456639147902,
             'type': 'integer'},
            {'25%': 0.0,
             '50%': 0.0,
             '75%': 0.0,
             'count': 4912.0,
             'index': 2,
             'max': 2.0,
             'mean': 0.14128664495114007,
             'min': 0.0,
             'name': 'gameNum',
             'std': 0.46806965450335747,
             'type': 'integer'},
            {'index': 3, 'name': 'gameID', 'type': 'string'},
            {'index': 4, 'name': 'teamID', 'type': 'string'},
            {'index': 5, 'name': 'lgID', 'type': 'string'},
            {'25%': 1.0,
             '50%': 1.0,
             '75%': 1.0,
             'count': 4875.0,
             'index': 6,
             'max': 1.0,
             'mean': 0.78174358974358971,
             'min': 0.0,
             'name': 'GP',
             'std': 0.41310477594222272,
             'type': 'number'},
            {'25%': 3.0,
             '50%': 5.0,
             '75%': 7.0,
             'count': 1540.0,
             'index': 7,
             'max': 10.0,
             'mean': 5.0519480519480515,
             'min': 0.0,
             'name': 'startingPos',
             'std': 2.646100537485232,
             'type': 'number'}
        ]
    }

def test_infer_schema_from_another_csv_file():
    '''Another sample CSV file test.'''

    path = '../test-data/test.csv'
    path = os.path.join(os.path.split(__file__)[0], path)
    abspath = os.path.abspath(path)

    schema = lib_csv.infer_schema_from_csv_file(abspath)

    fields = schema['fields']
    assert len(fields) == 6
    assert fields[0] == {'index': 0, 'name': 'datetime', 'type': 'string'}
    assert fields[1] == {'index': 1, 'name': 'timedelta', 'type': 'string'}
    assert fields[2]['25%'] == 10.0
    assert fields[2]['50%'] == 10.0
    assert fields[2]['75%'] == 10.0
    assert fields[2]['count'] == 1.0
    assert fields[2]['index'] == 2
    assert fields[2]['max'] == 10.0
    assert fields[2]['mean'] == 10.0
    assert fields[2]['min'] == 10.0
    assert fields[2]['name'] == 'integer'
    assert fields[2]['type'] == 'integer'
