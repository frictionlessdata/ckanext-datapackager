'''Unit tests for lib/helpers.py.

'''
import os.path
import StringIO

import mock

import ckanext.datapackager.lib.helpers as helpers
import ckanext.datapackager.exceptions as exceptions


def test_resource_display_name():
    '''Test that resource_display_name() changes "Unnamed resource" to
    "Unnamed file".

    '''
    resource_dict = {
        'name': None,
        'description': None
    }

    display_name = helpers.resource_display_name(resource_dict)

    assert display_name == "Unnamed file"


def test_csv_data_from_file_with_good_csv_file():
    '''Test _csv_data_from_file() with a good, 14-line CSV file.

    We expect to get only the first 10 rows back, and the rows should have
    been transformed from vertical into horizontal rows.

    '''
    csv = ('playerID,yearID,teamID,lgID,inseason,G,W,L,rank,plyrMgr\n'
           'wrighha01,1871,BS1,NA,1,31,20,10,3,Y\n'
           'woodji01,1871,CH1,NA,1,28,19,9,2,Y\n'
           'paborch01,1871,CL1,NA,1,29,10,19,8,Y\n'
           'lennobi01,1871,FW1,NA,1,14,5,9,8,Y\n'
           'deaneha01,1871,FW1,NA,2,5,2,3,8,Y\n'
           'fergubo01,1871,NY2,NA,1,33,16,17,5,Y\n'
           'mcbridi01,1871,PH1,NA,1,28,21,7,1,Y\n'
           'hastisc01,1871,RC1,NA,1,25,4,21,9,Y\n'
           'pikeli01,1871,TRO,NA,1,4,1,3,6,Y\n'
           'cravebi01,1871,TRO,NA,2,25,12,12,6,Y\n'
           'youngni99,1871,WS3,NA,1,32,15,15,4,N\n'
           'cravebi01,1872,BL1,NA,1,41,27,13,2,Y\n'
           'millsev01,1872,BL1,NA,2,17,8,6,2,Y\n')

    result = helpers._csv_data_from_file(StringIO.StringIO(csv))

    assert result['success'] is True
    assert len(result['data']) == 10
    assert result['data'][0] == ('playerID', 'wrighha01', 'woodji01',
                                 'paborch01', 'lennobi01', 'deaneha01',
                                 'fergubo01', 'mcbridi01', 'hastisc01',
                                 'pikeli01')
    assert result['data'][4] == ('inseason', '1', '1', '1', '1', '2', '1', '1',
                                 '1', '1')
    assert result['data'][9] == ('plyrMgr', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y',
                                 'Y', 'Y')


def test_csv_data_from_file_with_less_rows_than_preview_limit():
    csv = ('playerID,yearID,teamID,lgID,inseason,G,W,L,rank,plyrMgr\n'
           'wrighha01,1871,BS1,NA,1,31,20,10,3,Y\n'
           'woodji01,1871,CH1,NA,1,28,19,9,2,Y\n'
           'paborch01,1871,CL1,NA,1,29,10,19,8,Y\n'
           'lennobi01,1871,FW1,NA,1,14,5,9,8,Y\n'
           'deaneha01,1871,FW1,NA,2,5,2,3,8,Y\n'
           'millsev01,1872,BL1,NA,2,17,8,6,2,Y\n')

    result = helpers._csv_data_from_file(StringIO.StringIO(csv))

    assert result['success'] is True
    assert len(result['data']) == 10
    assert result['data'][0] == ('playerID', 'wrighha01', 'woodji01',
                                 'paborch01', 'lennobi01', 'deaneha01',
                                 'millsev01')
    assert result['data'][4] == ('inseason', '1', '1', '1', '1', '2', '2')
    assert result['data'][9] == ('plyrMgr', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y')


def test_csv_data_from_file_with_same_rows_as_preview_limit():
    csv = ('playerID,yearID,teamID,lgID,inseason,G,W,L,rank,plyrMgr\n'
           'wrighha01,1871,BS1,NA,1,31,20,10,3,Y\n'
           'woodji01,1871,CH1,NA,1,28,19,9,2,Y\n'
           'paborch01,1871,CL1,NA,1,29,10,19,8,Y\n'
           'lennobi01,1871,FW1,NA,1,14,5,9,8,Y\n'
           'deaneha01,1871,FW1,NA,2,5,2,3,8,Y\n'
           'fergubo01,1871,NY2,NA,1,33,16,17,5,Y\n'
           'mcbridi01,1871,PH1,NA,1,28,21,7,1,Y\n'
           'hastisc01,1871,RC1,NA,1,25,4,21,9,Y\n'
           'pikeli01,1871,TRO,NA,1,4,1,3,6,Y\n')

    result = helpers._csv_data_from_file(StringIO.StringIO(csv),
                                         preview_limit=10)

    assert result['success'] is True
    assert len(result['data']) == 10
    assert result['data'][0] == ('playerID', 'wrighha01', 'woodji01',
                                 'paborch01', 'lennobi01', 'deaneha01',
                                 'fergubo01', 'mcbridi01', 'hastisc01',
                                 'pikeli01')
    assert result['data'][4] == ('inseason', '1', '1', '1', '1', '2', '1', '1',
                                 '1', '1')
    assert result['data'][9] == ('plyrMgr', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y', 'Y',
                                 'Y', 'Y')


@mock.patch('__builtin__.open')
@mock.patch('ckanext.datapackager.lib.helpers._csv_data_from_file')
@mock.patch('ckanext.datapackager.lib.util.get_path_to_resource_file')
def test_csv_data_with_good_resource(mock_get_path_to_resource_file,
                                     mock_csv_data_from_file, mock_open):
    '''Test csv_data() with a good resource that has an uploaded CSV file.

    When given a resource dict for which get_path_to_resource_file() returns a
    path to a file, csv_data() should return the result of calling
    _csv_data_from_file() and passing it the path.

    '''
    # Make each of the mocked functions return constant values.
    mock_get_path_to_resource_file.return_value = 'path to resource file'
    mock_csv_data_from_file.return_value = 'csv data'
    mock_open.return_value = 'file data'

    mock_resource_dict = mock.Mock()

    result = helpers.csv_data(mock_resource_dict)

    # csv_data() should call get_path_to_resource_file() once, passing it the
    # resource dict.
    mock_get_path_to_resource_file.assert_called_once_with(
        mock_resource_dict)

    # csv_data() should call _csv_data_from_file() passing it the opened file.
    mock_csv_data_from_file.assert_called_once_with(
        mock_open.return_value)

    assert result == mock_csv_data_from_file.return_value, (
        "csv_data() should return what _csv_data_from_file() returns")


@mock.patch('ckanext.datapackager.lib.util.get_path_to_resource_file')
def test_csv_data_with_bad_resource(mock_get_path_to_resource_file):
    '''When called with a resource dict for which get_path_to_resource_file()
    raises ResourceFileDoesNotExistException,  csv_data() should return a
    dict with 'success': False and an error message.

    '''
    mock_get_path_to_resource_file.side_effect = (
        exceptions.ResourceFileDoesNotExistException)

    result = helpers.csv_data({})

    assert result == {'success': False,
                      'error': "There's no uploaded file for this resource"}
