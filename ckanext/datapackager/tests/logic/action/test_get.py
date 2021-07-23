'''Functional tests for logic/action/get.py.

'''

import pytest

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers

from ckan_datapackage_tools import converter
import ckan.plugins.toolkit as toolkit

@pytest.mark.ckan_config('ckan.plugins', 'datapackager')
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestGet():

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

        assert expected_output == datapackage_dict

    def test_package_show_as_datapackage_with_missing_id(self):
        with pytest.raises(toolkit.ValidationError):
            helpers.call_action('package_show_as_datapackage')
