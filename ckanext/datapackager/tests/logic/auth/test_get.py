import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers

import ckanext.datapackager.tests.helpers as custom_helpers

class TestPackageShowApi(custom_helpers.FunctionalTestBaseClass):
    def test_package_show_for_non_logged_in_user(self):
        user = factories.User()
        package = factories.Dataset(user=user)
        context = {'user': None, 'ignore_auth': False}
        helpers.call_action('package_show', context=context,
                            id=package['id'])
