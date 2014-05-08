import nose.tools as nt

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.tests.helpers as custom_helpers

class TestPackageUpdateApi(custom_helpers.FunctionalTestBaseClass):
    def test_user_can_update_package_they_own(self):
        user = factories.User()
        package = factories.Dataset(user=user)
        context = {
            'user': user['name'],
            'ignore_auth': False
        }
        helpers.call_action('package_update', context=context,
                            id=package['id'], schema='')

    def test_user_cannot_update_someone_elses_package(self):
        package = factories.Dataset(user=factories.User())
        context = {'user': factories.User()['name'], 'ignore_auth': False}
        nt.assert_raises(toolkit.NotAuthorized, helpers.call_action,
                         'package_update', context=context, id=package['id'],
                         schema='')

    def test_sysadmin_can_update_any_users_package(self):
        package = factories.Dataset(user=factories.User())
        context = {'user': factories.Sysadmin()['name'], 'ignore_auth': False}

        helpers.call_action('package_update', context=context,
                            id=package['id'], schema='')

class TestResourceUpdateApi(custom_helpers.FunctionalTestBaseClass):
    def test_user_can_update_resources_in_packages_they_own(self):
        user = factories.User()
        package = factories.Dataset(user=user)
        resource = factories.Resource(dataset=package, name='res')
        context = {
            'user': user['name'],
            'ignore_auth': False
        }
        helpers.call_action('resource_update', context=context,
                            id=resource['id'], name='res', url='url')

    def test_user_cannot_update_resources_in_someone_elses_package(self):
        package = factories.Dataset(user=factories.User())
        user = factories.User()
        resource = factories.Resource(dataset=package, name='res')
        context = {'user': user['name'], 'ignore_auth': False}
        nt.assert_raises(toolkit.NotAuthorized, helpers.call_action,
                         'resource_update', context=context,
                         id=resource['id'], name='res', url='url')
