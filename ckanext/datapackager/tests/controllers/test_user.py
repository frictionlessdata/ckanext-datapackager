'''Functional tests for controllers/user.py.'''

import ckan.new_tests.factories as factories
import ckanext.datapackager.tests.helpers as custom_helpers


class TestDataPackagerUserController(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackagerUserController class.'''

    def test_dashboard_not_logged_in(self):
        '''Test the redirect for not-logged-in users visiting /dashboard.

        If a not-logged-in user visits /dashboard, they should get redirected
        to the login page.

        '''
        response = self.app.get('/dashboard')
        assert response.status_int == 302
        assert '/user/login' in response.location

    def test_dashboard_logged_in(self):
        '''Test the redirect for logged-in users visiting /dashboard.

        If a logged-in user visits /dashboard, they should get redirected to
        their profile page.

        '''
        user = factories.User()

        response = self.app.get('/dashboard',
            extra_environ={'REMOTE_USER': str(user['name'])})
        assert response.status_int == 302
        assert '/user/{name}'.format(name=user['name']) in response.location
