'''Functional tests for controllers/package.py.'''
import os

import nose.tools as nt

import ckan.model as model
import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers
import ckanapi


class TestDataPackagerPackageController(
        custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackagerPackageController class.'''

    def test_add_package(self):
        '''Test the custom two-step add package process.

        CKAN's three-step add dataset process should be changed into a two-step
        process, with the user being redirected to the package read page after
        the second step.

        '''
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
        path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
        path = os.path.join(os.path.split(__file__)[0], path)
        abspath = os.path.abspath(path)

        # Fill out the form and submit it.
        form = response.forms[0]
        form['upload'] = ('upload', abspath)
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

        assert response.status_int == 200

        # Test that the package and resource were created.
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        package = api.action.package_show(id='my-test-package')
        assert package['title'] == 'my test package'
        assert package['state'] == 'active'
        resources = package['resources']
        assert len(resources) == 1

        # Test that the schema was inserted into the resource.
        # (Unit tests elsewhere test whether the contents of the schemas are
        # correct.)
        resource = resources[0]
        assert 'schema' in resource
        schema = resource['schema']
        assert 'fields' in schema

    def test_resource_schema_field(self):
        #create test package and resource
        usr = toolkit.get_action('get_site_user')({'model':model,'ignore_auth': True},{})
        upload = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=usr['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #render page
        response = self.app.get('/package/{0}/file/{1}/schema/0'.format(package['id'], resource['id']))

        #test that our snippet is rendered
        start = response.body.index('Snippet package/snippets/resource_schema_field.html start')
        end = response.body.index('Snippet package/snippets/resource_schema_field.html end')
        snippet = response.body[start:end]
        nt.assert_in('index', snippet)
        nt.assert_in('0', snippet)
        nt.assert_in('type', snippet)
        nt.assert_in('string', snippet)
        nt.assert_in('name', snippet)
        nt.assert_in('playerID', snippet)

        #check the list of links to other fields are in the secondary content
        start = response.body.index('Snippet package/snippets/resource_schema_list.html start')
        end = response.body.index('Snippet package/snippets/resource_schema_list.html end')
        snippet = response.body[start:end]
        nt.assert_in('playerID', snippet)
        nt.assert_in('yearID', snippet)
        nt.assert_in('gameNum', snippet)
        nt.assert_in('gameID', snippet)
        nt.assert_in('teamID', snippet)
        nt.assert_in('lgID', snippet)
        nt.assert_in('GP', snippet)
        nt.assert_in('startingPos', snippet)

    def test_resource_schema(self):
        #create test package and resource
        usr = toolkit.get_action('get_site_user')({'model':model,'ignore_auth': True},{})
        upload = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=usr['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #render page
        response = self.app.get('/package/{0}/file/{1}/schema'.format(package['id'], resource['id']))

        #test that our snippet is rendered
        start = response.body.index('Snippet package/snippets/resource_schema.html start')
        end = response.body.index('Snippet package/snippets/resource_schema.html end')
        snippet = response.body[start:end]

        # check that the list of schema fields have been rendered into our template
        nt.assert_in('playerID', snippet)
        nt.assert_in('yearID', snippet)
        nt.assert_in('gameNum', snippet)
        nt.assert_in('gameID', snippet)
        nt.assert_in('teamID', snippet)
        nt.assert_in('lgID', snippet)
        nt.assert_in('GP', snippet)
        nt.assert_in('startingPos', snippet)
