import nose.tools as nt

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.tests.helpers as custom_helpers

class TestPackageCreateApi(custom_helpers.FunctionalTestBaseClass):
    def test_anonymous_users_cannot_create_packages(self):
        context = {'user': None, 'ignore_auth': False}
        nt.assert_raises(toolkit.NotAuthorized, helpers.call_action,
                         'package_create', context=context, name='name',
                         title='title')

    def test_logged_in_users_can_create_packages(self):
        context = {'ignore_auth': False}
        helpers.call_action('package_create', context=context, name='name',
                         title='title')
