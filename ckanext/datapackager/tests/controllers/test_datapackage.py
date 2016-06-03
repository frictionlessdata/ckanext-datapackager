'''Functional tests for controllers/package.py.'''
import json

import nose.tools
import requests_mock
import ckanapi
import datapackage

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

    def test_download_datapackage(self):
        '''Test downloading a DataPackage file of a package.

        '''
        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        # Add a resource with a linked-to, not uploaded, data file.
        linked_resource = factories.Resource(
            package_id=dataset['id'],
            url='http://www.foo.com/data.csv',
            schema='{"fields":[{"type":"string", "name":"col1"}]}',
        )

        # Add a resource with an uploaded data file.
        csv_path = 'lahmans-baseball-database/AllstarFull.csv'
        csv_file = custom_helpers.get_csv_file(csv_path)
        uploaded_resource = api.action.resource_create(
            package_id=dataset['id'],
            name='AllstarFull',
            upload=csv_file,
            url=''  # FIXME: See https://github.com/ckan/ckan/issues/2769
        )

        # Download the package's JSON file.
        url = toolkit.url_for('export_datapackage',
                              package_id=dataset['name'])
        response = self.app.get(url)

        # Open and validate the response as a JSON.
        dp = datapackage.DataPackage(json.loads(response.body))
        dp.validate()

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], dp.metadata['name'])

        resources = dp.resources
        nose.tools.assert_equals(len(resources), 2)
        nose.tools.assert_equals(linked_resource['url'],
                                 resources[0].metadata['url'])
        schema = resources[0].metadata['schema']
        nose.tools.assert_equals(
            {'fields': [{'type': 'string', 'name': 'col1'}]}, schema)

        nose.tools.assert_equals(uploaded_resource['url'],
                                 resources[1].metadata['url'])
        nose.tools.assert_not_in('path', resources[1].metadata)

    def test_that_download_button_is_on_page(self):
        '''Tests that the download button is shown on the dataset pages.'''

        dataset = factories.Dataset()

        response = self.app.get('/dataset/{0}'.format(dataset['name']))
        soup = response.html
        download_button = soup.find(id='export_datapackage_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for('export_datapackage',
                                               package_id=dataset['name'])

    def test_new_renders(self):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_datapackage')
        response = self.app.get(url, extra_environ=env)
        assert_equals(200, response.status_int)

    @helpers.change_config('ckan.auth.create_unowned_dataset', False)
    def test_new_requires_user_to_be_able_to_create_packages(self):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_datapackage')
        response = self.app.get(url, extra_environ=env, status=[401])
        assert_true('Unauthorized to create a dataset' in response.body)

    @requests_mock.Mocker(real_http=True)
    def test_import_datapackage(self, mock_requests):
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
        mock_requests.register_uri('GET', datapackage_url, json=datapackage)

        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_datapackage', url=datapackage_url)
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
