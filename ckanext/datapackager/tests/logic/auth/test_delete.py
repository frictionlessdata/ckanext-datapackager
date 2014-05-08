import nose.tools as nt

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.tests.helpers as custom_helpers

class TestPackageDeleteApi(custom_helpers.FunctionalTestBaseClass):
    def test_user_can_delete_package_they_own(self):
        user = factories.User()
        package = factories.Dataset(user=user)
        context = {
            'user': user['name'],
            'ignore_auth': False
        }
        helpers.call_action('package_delete', context=context,
                            id=package['id'])

    def test_user_cannot_delete_someone_elses_package(self):
        package = factories.Dataset(user=factories.User())
        context = {'user': factories.User()['name'], 'ignore_auth': False}
        nt.assert_raises(toolkit.NotAuthorized, helpers.call_action,
                         'package_delete', context=context, id=package['id'])

    def test_sysadmin_can_delete_any_users_package(self):
        package = factories.Dataset(user=factories.User())
        context = {'user': factories.Sysadmin()['name'], 'ignore_auth': False}

        helpers.call_action('package_delete', context=context,
                            id=package['id'])
