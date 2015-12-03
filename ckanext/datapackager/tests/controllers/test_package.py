'''Functional tests for controllers/package.py.'''
import os
import zipfile
import StringIO
import json

import nose.tools
import ckanapi

import ckan.new_tests.factories as factories
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers


def _get_csv_file(relative_path):
        path = os.path.join(os.path.split(__file__)[0], relative_path)
        abspath = os.path.abspath(path)
        csv_file = open(abspath)
        return csv_file


class TestDataPackagerPackageController(
        custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackagerPackageController class.'''

    def test_download_tdf(self):
        '''Test downloading a Tabular Data Format ZIP file of a package.

        '''
        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        # Add a resource with a linked-to, not uploaded, data file.
        linked_resource = factories.Resource(package_id=dataset['id'],
            url='http://test.com/test-url-1',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        # Add a resource with an uploaded data file.
        csv_path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
        csv_file = _get_csv_file(csv_path)
        api.action.resource_create(
            package_id=dataset['id'],
            name='AllstarFull.csv',
            upload=csv_file,
            url=''  # FIXME: See https://github.com/ckan/ckan/issues/2769
        )

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
                                 ['AllstarFull.csv', 'datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])

        resources = datapackage['resources']
        nose.tools.assert_equals(linked_resource['url'], resources[0]['url'])
        schema = resources[0]['schema']
        nose.tools.assert_equals(
            {'fields': [{'type': 'string', 'name': 'col1'}]}, schema)

        nose.tools.assert_equals(resources[1]['path'], 'AllstarFull.csv')

        # Check the contenst of the AllstarFull.csv file.
        assert (zip_.open('AllstarFull.csv').read() ==
                _get_csv_file(csv_path).read())

    def test_download_tdf_with_three_files(self):
        '''Upload three CSV files to a package and test downloading the ZIP.'''

        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        def filename(path):
            return os.path.split(path)[1]

        csv_paths = ('../test-data/lahmans-baseball-database/AllstarFull.csv',
            '../test-data/lahmans-baseball-database/PitchingPost.csv',
            '../test-data/lahmans-baseball-database/TeamsHalf.csv')
        for path in csv_paths:
            csv_file = _get_csv_file(path)
            api.action.resource_create(
                package_id=dataset['id'],
                name=filename(path),
                upload=csv_file,
                url=''  # FIXME: See https://github.com/ckan/ckan/issues/2769
            )

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
            [filename(path) for path in csv_paths] + ['datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])
        resources = datapackage['resources']
        for csv_path, resource in zip(csv_paths, resources):
            nose.tools.assert_equals(resource['path'], filename(csv_path))

        # Check the contents of the CSV files.
        for csv_path in csv_paths:
            assert (zip_.open(filename(csv_path)).read() ==
                    _get_csv_file(csv_path).read())

    def test_that_download_button_is_on_page(self):
        '''Tests that the download button is shown on the dataset pages.'''

        dataset = factories.Dataset()

        response = self.app.get('/dataset/{0}'.format(dataset['name']))
        soup = response.html
        download_button = soup.find(id='download_tdf_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
