'''Functional tests for logic/action/get.py.

'''
import nose.tools

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckanext.datapackager.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit


class TestGet(custom_helpers.FunctionalTestBaseClass):

    def test_package_to_tabular_data_format(self):

        dataset = factories.Dataset()
        factories.Resource(package_id=dataset['id'], url='http://test.com/test-url-1',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')
        factories.Resource(package_id=dataset['id'], url='http://test.com/test-url-2',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        tdf = helpers.call_action('package_to_tabular_data_format',
                                  id=dataset['name'])

        expected_output = {
            'name': dataset['name'],
            'title': dataset['title'],
            'resources': [
                {
                    'schema': {
                        u'fields': [{u'name': u'col1', u'type': u'string'}]
                    },
                    'url': u'http://test.com/test-url-1'
                },
                {
                    'schema': {
                        u'fields': [{u'name': u'col1', u'type': u'string'}]
                    },
                    'url': u'http://test.com/test-url-2'
                }
            ]
        }
        nose.tools.assert_equals(expected_output, tdf)

    def test_package_to_tdf_with_missing_id(self):
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_to_tabular_data_format',
        )
