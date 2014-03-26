'''Functional tests for controllers/home.py

'''
import ckan.plugins.toolkit as toolkit

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
