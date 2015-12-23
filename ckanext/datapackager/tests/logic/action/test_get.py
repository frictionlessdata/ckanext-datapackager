'''Functional tests for logic/action/get.py.

'''
import nose.tools

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.datapackager.tests.helpers as custom_helpers
import ckanext.datapackager.lib.converter as converter
import ckan.plugins.toolkit as toolkit


class TestGet(custom_helpers.FunctionalTestBaseClass):

    def test_package_show_as_datapackage(self):

        dataset = factories.Dataset()
        factories.Resource(package_id=dataset['id'], url='http://test.com/test-url-1',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')
        factories.Resource(package_id=dataset['id'], url='http://test.com/test-url-2',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        expected_output = converter.dataset_to_datapackage(
            helpers.call_action('package_show', id=dataset['id'])
        )

        datapackage_dict = helpers.call_action('package_show_as_datapackage',
                                               id=dataset['name'])

        nose.tools.assert_items_equal(expected_output, datapackage_dict)

    def test_package_show_as_datapackage_with_missing_id(self):
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_show_as_datapackage',
        )
