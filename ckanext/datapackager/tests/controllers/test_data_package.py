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

assert_equals = nose.tools.assert_equals
assert_true = nose.tools.assert_true
assert_regexp_matches = nose.tools.assert_regexp_matches


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

    def test_new_renders(self):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_data_package')
        response = self.app.get(url, extra_environ=env)
        assert_equals(200, response.status_int)

    @helpers.change_config('ckan.auth.anon_create_dataset', False)
    def test_new_requires_user_to_be_able_to_create_packages(self):
        url = toolkit.url_for('import_data_package')
        response = self.app.get(url)
        assert_equals(302, response.status_int)
        assert_true('Unauthorized to create a package' in response.follow())

    @httpretty.activate
    def test_import_data_package(self):
        httpretty.HTTPretty.allow_net_connect = False
        datapackage_url = 'http://www.foo.com/datapackage.json'
        datapackage = {
            'name': 'foo',
            'resources': [
                {
                    'name': 'the-resource',
                    'url': 'http://www.somewhere.com/data.csv',
                }
            ]
        }
        httpretty.register_uri(httpretty.GET, datapackage_url,
                               body=json.dumps(datapackage))
        httpretty.register_uri(httpretty.GET, datapackage['resources'][0]['url'])

        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_data_package', url=datapackage_url)
        response = self.app.post(
            url,
            extra_environ=env,
        )
        # Should redirect to dataset's page
        assert_equals(response.status_int, 302)
        assert_regexp_matches(response.headers['Location'], '/dataset/foo$')

        # Should create the dataset
        dataset = helpers.call_action('package_show', id=datapackage['name'])
        assert_equals(dataset['name'], 'foo')
        assert_equals(len(dataset.get('resources', [])), 1)
        assert_equals(dataset['resources'][0].get('name'), 'the-resource')
        assert_equals(dataset['resources'][0].get('url'),
                      datapackage['resources'][0]['url'])
