import json
import httpretty
import nose.tools
import tempfile
import mock

import ckan.tests.helpers as helpers
import ckanext.datapackager.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit
import ckan.tests.factories as factories


class TestPackageCreateFromDataPackage(custom_helpers.FunctionalTestBaseClass):
    def test_it_requires_a_url_if_theres_no_upload_param(self):
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
        )

    @httpretty.activate
    def test_it_raises_if_datapackage_is_invalid(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {}
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url,
        )

    @httpretty.activate
    def test_it_raises_if_datapackage_is_unsafe(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'unsafe',
            'resources': [
                {
                    'name': 'unsafe-resource',
                    'path': '/etc/shadow',
                }
            ]
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url,
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
            ],
            'some_extra_data': {'foo': 'bar'},
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))
        # FIXME: Remove this when
        # https://github.com/okfn/datapackage-py/issues/20 is done
        httpretty.register_uri(httpretty.GET,
                               datapackage['resources'][0]['url'])

        dataset = helpers.call_action('package_create_from_datapackage',
                                      url=url)

        extras = dataset['extras']
        nose.tools.assert_equal(extras[0]['key'], 'some_extra_data')
        nose.tools.assert_dict_equal(json.loads(extras[0]['value']),
                                     datapackage['some_extra_data'])

        resource = dataset.get('resources')[0]
        nose.tools.assert_equal(resource['name'],
                                datapackage['resources'][0]['name'])
        nose.tools.assert_equal(resource['url'],
                                datapackage['resources'][0]['url'])

    @httpretty.activate
    def test_it_creates_a_dataset_without_resources(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo'
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id=datapackage['name'])
        nose.tools.assert_equal(dataset['state'], 'active')

    @mock.patch('ckanext.datapackager.logic.action.create._create_and_upload_resource')
    @httpretty.activate
    def test_it_purges_the_dataset_if_there_was_some_error_creating_resources(self, _create_and_upload_resource_mock):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.zip'
        datapkg_path = custom_helpers.fixture_path('datetimes-datapackage.zip')
        with open(datapkg_path, 'rb') as f:
            httpretty.register_uri(httpretty.GET, url, body=f.read())

        _create_and_upload_resource_mock.side_effect = IOError
        original_datasets = helpers.call_action('package_list')

        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url
        )

        new_datasets = helpers.call_action('package_list')
        nose.tools.assert_equal(original_datasets, new_datasets)

    @httpretty.activate
    def test_it_uploads_local_files(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.zip'
        datapkg_path = custom_helpers.fixture_path('datetimes-datapackage.zip')
        with open(datapkg_path, 'rb') as f:
            httpretty.register_uri(httpretty.GET, url, body=f.read())

        # FIXME: Remove this when
        # https://github.com/okfn/datapackage-py/issues/20 is done
        timezones_url = 'https://www.somewhere.com/timezones.csv'
        httpretty.register_uri(httpretty.GET, timezones_url, body='')

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='datetimes')
        resources = dataset.get('resources')

        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        nose.tools.assert_regexp_matches(resources[0]['url'], 'datetimes.csv$')

    @httpretty.activate
    def test_it_uploads_resources_with_inline_strings_as_data(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
            'resources': [
                {
                    'name': 'the-resource',
                    'data': 'inline data',
                }
            ]
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='foo')
        resources = dataset.get('resources')

        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        nose.tools.assert_true(resources[0]['name'] in resources[0]['url'])

    @httpretty.activate
    def test_it_uploads_resources_with_inline_dicts_as_data(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
            'resources': [
                {
                    'name': 'the-resource',
                    'data': {'foo': 'bar'},
                }
            ]
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='foo')
        resources = dataset.get('resources')

        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        nose.tools.assert_true(resources[0]['name'] in resources[0]['url'])

    @httpretty.activate
    def test_it_allows_specifying_the_dataset_name(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        dataset = helpers.call_action('package_create_from_datapackage',
                                      url=url,
                                      name='bar')
        nose.tools.assert_equal(dataset['name'], 'bar')

    @httpretty.activate
    def test_it_creates_unique_name_if_name_wasnt_specified(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        helpers.call_action('package_create', name=datapackage['name'])
        dataset = helpers.call_action('package_create_from_datapackage',
                                      url=url)
        nose.tools.assert_true(dataset['name'].startswith('foo'))

    @httpretty.activate
    def test_it_fails_if_specifying_name_that_already_exists(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        helpers.call_action('package_create', name=datapackage['name'])
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url,
            name=datapackage['name']
        )

    @httpretty.activate
    def test_it_allows_changing_dataset_visibility(self):
        httpretty.HTTPretty.allow_net_connect = False
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        httpretty.register_uri(httpretty.GET, url,
                               body=json.dumps(datapackage))

        user = factories.Sysadmin()
        organization = factories.Organization()
        dataset = helpers.call_action('package_create_from_datapackage',
                                      context={'user': user['id']},
                                      url=url,
                                      owner_org=organization['id'],
                                      private=True)
        nose.tools.assert_true(dataset['private'])

    def test_it_allows_uploading_a_datapackage(self):
        class _UploadFile(object):
            '''Mock the parts from cgi.FileStorage we use.'''
            def __init__(self, fp):
                self.file = fp

        datapackage = {
            'name': 'foo',
        }
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(json.dumps(datapackage))
            tmpfile.flush()

            dataset = helpers.call_action('package_create_from_datapackage',
                                          upload=_UploadFile(tmpfile))
            nose.tools.assert_equal(dataset['name'], 'foo')
