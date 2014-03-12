'''Functional tests for controllers/package.py.'''
import os.path

import ckan.new_tests.factories as factories
import ckanext.b2.tests.helpers as custom_helpers
import ckanapi


class TestB2PackageController(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the B2PackageController class.'''

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
