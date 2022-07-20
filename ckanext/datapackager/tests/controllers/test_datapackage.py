'''Functional tests for controllers/package.py.'''
import json
import pytest
import responses
from bs4 import BeautifulSoup
import re

import ckanapi
import datapackage
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers

responses.add_passthru(toolkit.config['solr_url'])

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
        url = toolkit.url_for('datapackager.export_datapackage',
                              package_id=dataset['name'])
        response = app.get(url)

        # Open and validate the response as a JSON.
        dp = datapackage.DataPackage(json.loads(response.body))
        dp.validate()

        # Check the contents of the datapackage.json file.
        assert dataset['name'] == dp.descriptor['name']

        resources = dp.resources
        assert len(resources) == 2
        assert linked_resource['url'] == resources[0].descriptor['path']
        assert linked_resource['url'] == resources[0].source
        schema = resources[0].schema
        assert schema.descriptor['fields'][0]['name'] == 'col1'
        assert schema.descriptor['fields'][0]['type'] == 'string'

        assert uploaded_resource['url'] == resources[1].descriptor['path']

    def test_that_download_button_is_on_page(self, app):
        '''Tests that the download button is shown on the dataset pages.'''

        dataset = factories.Dataset()

        response = app.get('/dataset/{0}'.format(dataset['name']))
        soup = BeautifulSoup(response.body)
        download_button = soup.find(id='export_datapackage_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for('datapackager.export_datapackage',
                                               package_id=dataset['id'])

    def test_new_renders(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('datapackager.import_datapackage')
        response = app.get(url, extra_environ=env)
        assert 200 == response.status_code

    @pytest.mark.ckan_config('ckan.auth.create_unowned_dataset', False)
    def test_new_requires_user_to_be_able_to_create_packages(self, app):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('datapackager.import_datapackage')
        response = app.get(url, extra_environ=env, status=401)
        assert 'Unauthorized to create a dataset' in response.body

    @responses.activate
    def test_import_datapackage(self, app):
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
        responses.add('GET', datapackage_url, json=datapackage)

        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('datapackager.import_datapackage', url=datapackage_url)
        response = app.post(
            url,
            extra_environ=env,
            follow_redirects=False
        )
        # Should redirect to dataset's page
        assert response.status_code == 302
        assert re.match('.*/dataset/foo$', response.headers['Location'])

        ## Should create the dataset
        dataset = helpers.call_action('package_show', id=datapackage['name'])
        assert dataset['name'] == 'foo'
        assert len(dataset.get('resources', [])) == 1
        assert dataset['resources'][0].get('name') == 'the-resource'
        assert (dataset['resources'][0].get('url') == datapackage['resources'][0]['url'])
