'''Functional tests for plugin.py.

'''
import os.path
import mock

import nose.tools

import ckanapi
import ckan.new_tests.factories as factories
import ckan.common as common
import ckanext.datapackager.tests.helpers as custom_helpers


class TestPlugin(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for DataPackagerPlugin.

    '''
    def test_resource_create(self):
        '''Test that a schema is added to a resource when it's created.

        Unit tests elsewhere test that the schemas inferred from CSV files are
        correct, here we're just testing that the schema gets added to the
        resource on resource_create().

        '''
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        csv_file = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')

        api.action.resource_create(package_id=package['id'],
                                   name='test-resource', upload=csv_file)

        # Apparently resource_create doesn't return the resource dict when
        # called via ckanapi, so we need another call to get it.
        package = api.action.package_show(id=package['id'])

        # The package should have just one resource, the one we just created.
        assert len(package['resources']) == 1
        resource = package['resources'][0]

        # There should be a schema in the resource.
        assert 'schema' in resource
        assert 'fields' in resource['schema']

    def test_resource_update(self):
        '''Test that a resource's schema is updated when the resource is
        updated with a new uploaded CSV file.

        Unit tests elsewhere test that the schemas inferred from CSV files are
        correct, here we're just testing that the schema gets added to the
        resource on resource_create().

        '''
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        # Upload a first CSV file to the package.
        csv_file = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        api.action.resource_create(package_id=package['id'],
                                   name='test-package', upload=csv_file)

        # Get the generated schema from the resource.
        package = api.action.package_show(id=package['id'])
        assert len(package['resources']) == 1
        resource = package['resources'][0]
        assert 'schema' in resource
        original_schema = resource['schema']

        # Now update the resource with a new file.
        csv_file = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/Appearances.csv')
        api.action.resource_update(id=resource['id'], name=resource['name'],
                                   upload=csv_file)

        # Check that the schema has been changed.
        package = api.action.package_show(id=package['id'])
        assert len(package['resources']) == 1
        resource = package['resources'][0]
        assert 'schema' in resource
        schema = resource['schema']
        assert 'fields' in schema
        assert schema != original_schema


    def test_schema_output_is_json_string(self):
        '''Test that a resource's schema output is a valid json string'''
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        csv_file = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        resource = api.action.resource_create(package_id=package['id'],
                                              name='test-resource',
                                              upload=csv_file)
        resource_show = api.action.resource_show(id=resource['id'])

        #try and load the schema as json string
        print resource_show['schema']
        common.json.loads(resource_show['schema'])

    @mock.patch('ckanext.datapackager.lib.csv_utils.infer_schema_from_csv_file')
    def test_user_is_warned_when_uploading_a_non_csv_file(self, mock):
        mock.side_effect = UnicodeDecodeError('','',1,1,'')

        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}
        package_title = 'my test package'
        package_name = 'my-test-package'

        # Get the new package page (first form).
        response = self.app.get('/package/new', extra_environ=extra_environ)
        assert response.status_int == 200

        # Fill out the form and submit it.
        form = response.forms[0]
        form['title'] = package_title
        form['name'] = package_name
        form['version'] = '0.1beta'
        form['notes'] = 'Just a test package nothing to see here'
        response = form.submit('save', extra_environ=extra_environ)

        # Follow the redirect to the second form.
        assert response.status_int == 302
        response = response.follow(extra_environ=extra_environ)

        assert response.status_int == 200

        # Get the CSV file to upload.
        path = './test-data/spacer.gif'
        path = os.path.join(os.path.split(__file__)[0], path)
        
        abspath = os.path.abspath(path)

        # Fill out the form and submit it.
        form = response.forms[0]
        form['upload'] = ('upload', open(abspath).read())
        form['name'] = 'My test CSV file'
        response = form.submit('save', extra_environ=extra_environ)


        # Follow the redirect to the third form.
        assert response.status_int == 302
        assert '/dataset/new_metadata/my-test-package' in response.location, response.location
        response = response.follow(extra_environ=extra_environ)

        # The third form immediately redirects you to the dataset read page.
        assert response.status_int == 302
        assert '/package/my-test-package' in response.location
        response = response.follow(extra_environ=extra_environ)

        nose.tools.assert_in('does not seem to be a csv or text', response.body)
        nose.tools.assert_in('Failed to calculate', response.body)
