import httpretty
import nose.tools

import ckan.tests.helpers as helpers
import ckanext.datapackager.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit


class TestPackageCreateFromDataPackage(custom_helpers.FunctionalTestBaseClass):
    def test_it_requires_a_url(self):
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
        )

    @httpretty.activate
    def test_it_creates_the_dataset(self):
        url = 'http://www.somewhere.com/datapackage.json'
        body = '{"name": "foo"}'
        httpretty.register_uri(httpretty.GET, url, body=body)

        helpers.call_action('package_create_from_datapackage', url=url)
        helpers.call_action('package_show', id='foo')
