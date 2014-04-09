'''Unit tests for lib/csv_utils.py.

'''
import os.path
import StringIO

import nose.tools

import ckanext.datapackager.lib.csv_utils as csv_utils


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

    schema = csv_utils.infer_schema_from_csv_file(abspath)

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

    schema = csv_utils.infer_schema_from_csv_file(abspath)

    fields = schema['fields']
    assert len(fields) == 7
    assert fields[0] == {'index': 0, 'name': 'datetime', 'type': 'string'}
    assert fields[1]['index'] == 1
    assert fields[1]['name'] == 'timedelta'
    assert fields[1]['type'] == 'string'
    assert fields[2]['index'] == 2
    assert fields[2]['name'] == 'integer'
    assert fields[2]['type'] == 'integer'


def test_temporal_extent_MM_DD_YY():
    '''Test temporal_extent() with MM-DD-YY-formatted date strings.

    '''
    csv_text = ('number,date\n'
                '0,06-23-17\n'
                '1,07-23-17\n'
                '2,012-13-23')
    csv_file = StringIO.StringIO(csv_text)

    extent = csv_utils.temporal_extent(csv_file, column_num=1)

    assert extent == '2017-06-23T00:00:00/2023-12-13T00:00:00'


def test_temporal_extent_YYYY():
    '''Test temporal_extent() with YYYY-formatted (year only) date strings.

    '''
    csv_text = ('number,date\n'
                '0,1933\n'
                '1,1997\n'
                '2,2016')
    csv_file = StringIO.StringIO(csv_text)

    extent = csv_utils.temporal_extent(csv_file, column_num=1)

    assert extent == '1933-01-01T00:00:00/2016-01-01T00:00:00'


def test_temporal_extent_with_all_non_date_values():
    '''temporal_extent() should raise ValueError if given data with all
    non-date values.

    '''
    csv_text = ('number,date\n'
                '0,foo\n'
                '1,bar\n'
                '2,gar')
    csv_file = StringIO.StringIO(csv_text)

    nose.tools.assert_raises(ValueError, csv_utils.temporal_extent, csv_file,
                             column_num=1)


def test_temporal_extent_with_some_date_values():
    '''temporal_extent() should raise ValueError if given data containing some
    dates and some non-date values.

    '''
    csv_text = ('number,date\n'
                '0,1933\n'
                '1,bar\n'
                '2,2007')
    csv_file = StringIO.StringIO(csv_text)

    nose.tools.assert_raises(ValueError, csv_utils.temporal_extent, csv_file,
                             column_num=1)


def test_temporal_extent_with_timezone():
    '''If given dates with timezones in the input data, temporal_extent()
    should output dates with UTC offsets.

    '''
    csv_text = ('number,date\n'
                '1,Fri Sep 26 11:22:13 CET 2007\n'
                '2,Sun Sep 28 09:11:45 CET 2007\n'
                '0,Thu Sep 25 10:36:28 CET 2007\n')
    csv_file = StringIO.StringIO(csv_text)

    extent = csv_utils.temporal_extent(csv_file, column_num=1)

    assert extent == '2007-09-25T10:36:28+02:00/2007-09-28T09:11:45+02:00'


def test_temporal_extent_with_mixed_naive_and_aware_dates():
    '''temporal_extent() should raise TypeError if given data containing both
    timezone-naive and timezone-aware datetimes.

    '''
    csv_text = ('number,date\n'
                '1,Fri Sep 26 11:22:13 CET 2007\n'
                '2,Sun Sep 28 09:11:45 2007\n'
                '0,Thu Sep 25 10:36:28 CKT 2007\n')
    csv_file = StringIO.StringIO(csv_text)

    nose.tools.assert_raises(TypeError, csv_utils.temporal_extent, csv_file,
                             column_num=1)


def test_temporal_extent_with_mixed_timezones():

    csv_text = ('number,date\n'
                '1,Fri Sep 26 11:22:13 CET 2007\n'
                '2,Sun Sep 28 09:11:45 GMT 2007\n'
                '0,Thu Sep 25 10:36:28 CET 2007\n')
    csv_file = StringIO.StringIO(csv_text)

    extent = csv_utils.temporal_extent(csv_file, column_num=1)
    assert extent == '2007-09-25T10:36:28+02:00/2007-09-28T09:11:45+00:00'


def test_temporal_extent_with_nonexistent_path():

    nose.tools.assert_raises(IOError, csv_utils.temporal_extent,
                             '/foo/bar/fsdfs/fdsfsd', column_num=1)


def test_temporal_extent_with_noncsv_file():

    nose.tools.assert_raises(IOError, csv_utils.temporal_extent,
                             '../test-data/not-a-csv.png', column_num=1)


def test_temporal_extent_with_invalid_path():

    nose.tools.assert_raises(IOError, csv_utils.temporal_extent,
                             path={'foo': 'bar'}, column_num=1)


def test_temporal_extent_with_nonexistent_index():

    csv_text = ('number,date\n'
                '1,Fri Sep 26 11:22:13 CET 2007\n'
                '2,Sun Sep 28 09:11:45 GMT 2007\n'
                '0,Thu Sep 25 10:36:28 CET 2007\n')
    csv_file = StringIO.StringIO(csv_text)

    nose.tools.assert_raises(IndexError, csv_utils.temporal_extent, csv_file,
                             column_num=6)


def test_temporal_extent_with_invalid_index():

    csv_text = ('number,date\n'
                '1,Fri Sep 26 11:22:13 CET 2007\n'
                '2,Sun Sep 28 09:11:45 GMT 2007\n'
                '0,Thu Sep 25 10:36:28 CET 2007\n')
    csv_file = StringIO.StringIO(csv_text)

    nose.tools.assert_raises(ValueError, csv_utils.temporal_extent, csv_file,
                             column_num={'foo': 'bar'})
