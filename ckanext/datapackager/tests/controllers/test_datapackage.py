'''Functional tests for controllers/package.py.'''
import json

import nose.tools
import datapackage
import pytest

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers


from bs4 import BeautifulSoup

assert_equals = nose.tools.assert_equals
assert_true = nose.tools.assert_true
assert_regexp_matches = nose.tools.assert_regexp_matches


@pytest.mark.ckan_config('ckan.plugins', 'datapackager')
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestDataPackageController():
    '''Functional tests for the DataPackageController class.'''

    def test_download_datapackage(self, app):
        '''Test downloading a DataPackage file of a package.

        '''
        user = factories.Sysadmin()
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
        uploaded_resource = helpers.call_action('resource_create', {},
            package_id=dataset['id'],
            name='AllstarFull',
            url='_needed_for_ckan<2.6',
            upload=csv_file,
        )

        # Download the package's JSON file.
        url = toolkit.url_for('export_datapackage',
                              package_id=dataset['name'])
        response = app.get(url)

        # Open and validate the response as a JSON.
        dp = datapackage.DataPackage(json.loads(response.body))
        dp.validate()

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], dp.descriptor['name'])

        resources = dp.resources
        nose.tools.assert_equals(len(resources), 2)
        nose.tools.assert_equals(linked_resource['url'],
                                 resources[0].descriptor['path'])
        nose.tools.assert_equals(linked_resource['url'],
                                 resources[0].source)
        schema = resources[0].schema
        nose.tools.assert_equals(
            schema.descriptor['fields'][0]['name'], 'col1')
        nose.tools.assert_equals(
            schema.descriptor['fields'][0]['type'], 'string')

        nose.tools.assert_equals(uploaded_resource['url'],
                                 resources[1].descriptor['path'])

    def test_that_download_button_is_on_page(self, app):
        '''Tests that the download button is shown on the dataset pages.'''

        dataset = factories.Dataset()

        response = app.get('/dataset/{0}'.format(dataset['name']))
        soup = BeautifulSoup(response.body)
        download_button = soup.find(id='export_datapackage_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for('export_datapackage',
                                               package_id=dataset['name'])

    def test_new_renders(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_datapackage')
        response = app.get(url, extra_environ=env)
        assert 200 == response.status_int

    @helpers.change_config('ckan.auth.create_unowned_dataset', False)
    def test_new_requires_user_to_be_able_to_create_packages(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_datapackage')
        response = app.get(url, extra_environ=env, status=[401])
        assert 'Unauthorized to create a dataset' in response.body

    def test_import_datapackage(self, requests_mock, app):
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
        requests_mock.register_uri('GET', datapackage_url, json=datapackage)

        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_datapackage', url=datapackage_url)
        response = app.post(
            url,
            extra_environ=env,
        )
        # Should redirect to dataset's page
        assert response.status_int == 302
        assert_regexp_matches(response.headers['Location'], '/dataset/foo$')

        # Should create the dataset
        dataset = helpers.call_action('package_show', id=datapackage['name'])
        assert dataset['name'] == 'foo'
        assert len(dataset.get('resources', [])) == 1
        assert dataset['resources'][0].get('name') == 'the-resource'
        assert (dataset['resources'][0].get('url') ==
                      datapackage['resources'][0]['url'])
