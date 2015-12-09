import json
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
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
            'resources': [
                {
                    'name': 'the-resource',
                    'url': 'http://www.somewhere.com/data.csv',
                }
            ]
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))
        # FIXME: Remove this when
        # https://github.com/okfn/datapackage-py/issues/20 is done
        httpretty.register_uri(httpretty.GET, datapackage['resources'][0]['url'])

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='foo')
        resource = dataset.get('resources')[0]
        nose.tools.assert_equal(resource['name'],
                                datapackage['resources'][0]['name'])
        nose.tools.assert_equal(resource['url'],
                                datapackage['resources'][0]['url'])
