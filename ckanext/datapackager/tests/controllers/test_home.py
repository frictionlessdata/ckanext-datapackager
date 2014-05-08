'''Functional tests for controllers/home.py

'''
import nose.tools as nt
import ckan.plugins.toolkit as toolkit
import ckan.new_tests.factories as factories

import ckanext.datapackager.tests.helpers as helpers


class TestDataPackagerHomeController(helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackagerHomeController class.'''

    def test_about_page(self):
        '''Test that the about page loads without crashing.

        '''
        response = self.app.get(toolkit.url_for('about'))
        assert response.status_int == 200

    def test_api_page(self):
        '''Test that the API page loads without crashing.

        '''
        response = self.app.get(toolkit.url_for('api'))
        assert response.status_int == 200

    def test_front_page_not_logged_in(self):
        '''Test that Register and Login buttons appear'''
        response = self.app.get(toolkit.url_for('home'))
        nt.assert_true('Login' in response.body)
        nt.assert_true('Register' in response.body)

    def test_front_page_logged_in_no_packages(self):
        '''Test that Add package button appears'''
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}
        response = self.app.get('/', extra_environ=extra_environ)
        nt.assert_true('Add new package' in response.body)

    def test_front_page_logged_in(self):
        '''Test that Add package and see package buttons appear'''
        user = factories.User()
        factories.Dataset(user=user)
        extra_environ = {'REMOTE_USER': str(user['name'])}
        response = self.app.get('/', extra_environ=extra_environ)
        nt.assert_true('Add new package' in response.body)
        nt.assert_true('See your packages' in response.body)
