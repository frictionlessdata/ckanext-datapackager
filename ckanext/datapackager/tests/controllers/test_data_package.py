'''Functional tests for controllers/package.py.'''
import os
import zipfile
import StringIO
import json

import nose.tools
import httpretty
import ckanapi

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers


class TestDataPackageController(
        custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackageController class.'''

    @httpretty.activate
    def test_download_tdf(self):
        '''Test downloading a Tabular Data Format ZIP file of a package.

        '''
        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        # Add a resource with a linked-to, not uploaded, data file.
        url = 'http://www.foo.com/data.csv'
        httpretty.register_uri(httpretty.GET, url, body='foo')
        linked_resource = factories.Resource(package_id=dataset['id'],
            url=url,
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        # Add a resource with an uploaded data file.
        csv_path = 'lahmans-baseball-database/AllstarFull.csv'
        csv_file = custom_helpers.get_csv_file(csv_path)
        api.action.resource_create(
            package_id=dataset['id'],
            name='AllstarFull',
            upload=csv_file,
            url=''  # FIXME: See https://github.com/ckan/ckan/issues/2769
        )

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.data_package:DataPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
                                 ['data/allstarfull.csv', 'datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])

        resources = datapackage['resources']
        nose.tools.assert_equals(linked_resource['url'], resources[0]['url'])
        schema = resources[0]['schema']
        nose.tools.assert_equals(
            {'fields': [{'type': 'string', 'name': 'col1'}]}, schema)

        nose.tools.assert_equals(resources[1]['path'], 'data/allstarfull.csv')

        # Check the contents of the allstarfull.csv file.
        assert (zip_.open('data/allstarfull.csv').read() ==
                custom_helpers.get_csv_file(csv_path).read())

    def test_download_tdf_with_three_files(self):
        '''Upload three CSV files to a package and test downloading the ZIP.'''

        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        def filename_without_format(path):
            return os.path.split(path)[1].split('.')[0].lower()

        def filename_inside_package(path):
            filename = '.'.join([filename_without_format(path), 'csv'])
            return os.path.join('data', filename)

        csv_paths = ('lahmans-baseball-database/AllstarFull.csv',
            'lahmans-baseball-database/PitchingPost.csv',
            'lahmans-baseball-database/TeamsHalf.csv')
        for path in csv_paths:
            csv_file = custom_helpers.get_csv_file(path)
            api.action.resource_create(
                package_id=dataset['id'],
                name=filename_without_format(path),
                format='csv',
                upload=csv_file,
                url=''  # FIXME: See https://github.com/ckan/ckan/issues/2769
            )

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.data_package:DataPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
            [filename_inside_package(path) for path in csv_paths] + ['datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])
        resources = datapackage['resources']
        for csv_path, resource in zip(csv_paths, resources):
            nose.tools.assert_equals(resource['path'], filename_inside_package(csv_path))

        # Check the contents of the CSV files.
        for csv_path in csv_paths:
            assert (zip_.open(filename_inside_package(csv_path)).read() ==
                    custom_helpers.get_csv_file(csv_path).read())

    def test_that_download_button_is_on_page(self):
        '''Tests that the download button is shown on the dataset pages.'''

        dataset = factories.Dataset()

        response = self.app.get('/dataset/{0}'.format(dataset['name']))
        soup = response.html
        download_button = soup.find(id='download_tdf_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for(
            controller='ckanext.datapackager.controllers.data_package:DataPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
