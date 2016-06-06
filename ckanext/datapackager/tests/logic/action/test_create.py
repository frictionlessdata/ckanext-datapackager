import json

import nose.tools
import tempfile
import requests_mock

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

    @requests_mock.Mocker(real_http=True)
    def test_it_raises_if_datapackage_is_invalid(self, mock_requests):
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {}
        mock_requests.register_uri('GET', url, json=datapackage)

        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url,
        )

    @requests_mock.Mocker(real_http=True)
    def test_it_raises_if_datapackage_is_unsafe(self, mock_requests):
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
        mock_requests.register_uri('GET', url, json=datapackage)

        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url,
        )

    @requests_mock.Mocker(real_http=True)
    def test_it_creates_the_dataset(self, mock_requests):
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
        mock_requests.register_uri('GET', url, json=datapackage)
        # FIXME: Remove this when
        # https://github.com/okfn/datapackage-py/issues/20 is done
        mock_requests.register_uri('GET',
                                   datapackage['resources'][0]['url'])

        dataset = helpers.call_action('package_create_from_datapackage',
                                      url=url)
        nose.tools.assert_equal(dataset['state'], 'active')

        extras = dataset['extras']
        nose.tools.assert_equal(extras[0]['key'], 'some_extra_data')
        nose.tools.assert_dict_equal(json.loads(extras[0]['value']),
                                     datapackage['some_extra_data'])

        resource = dataset.get('resources')[0]
        nose.tools.assert_equal(resource['name'],
                                datapackage['resources'][0]['name'])
        nose.tools.assert_equal(resource['url'],
                                datapackage['resources'][0]['url'])

    @requests_mock.Mocker(real_http=True)
    def test_it_creates_a_dataset_without_resources(self, mock_requests):
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo'
        }
        mock_requests.register_uri('GET', url, json=datapackage)

        helpers.call_action('package_create_from_datapackage', url=url)

        helpers.call_action('package_show', id=datapackage['name'])

    def test_it_deletes_dataset_on_error_when_creating_resources(self):
        datapkg_path = custom_helpers.fixture_path(
            'datetimes-datapackage-with-inexistent-resource.zip'
        )

        original_datasets = helpers.call_action('package_list')

        with open(datapkg_path, 'rb') as datapkg:
            nose.tools.assert_raises(
                toolkit.ValidationError,
                helpers.call_action,
                'package_create_from_datapackage',
                upload=_UploadFile(datapkg),
            )

        new_datasets = helpers.call_action('package_list')
        nose.tools.assert_equal(original_datasets, new_datasets)

    @requests_mock.Mocker(real_http=True)
    def test_it_uploads_local_files(self, mock_requests):
        url = 'http://www.somewhere.com/datapackage.zip'
        datapkg_path = custom_helpers.fixture_path('datetimes-datapackage.zip')
        with open(datapkg_path, 'rb') as f:
            mock_requests.register_uri('GET', url, content=f.read())

        # FIXME: Remove this when
        # https://github.com/okfn/datapackage-py/issues/20 is done
        timezones_url = 'https://www.somewhere.com/timezones.csv'
        mock_requests.register_uri('GET', timezones_url, text='')

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='datetimes')
        resources = dataset.get('resources')

        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        nose.tools.assert_regexp_matches(resources[0]['url'], 'datetimes.csv$')

    @requests_mock.Mocker(real_http=True)
    def test_it_uploads_resources_with_inline_strings_as_data(self,
                                                              mock_requests):
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
        mock_requests.register_uri('GET', url, json=datapackage)

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='foo')
        resources = dataset.get('resources')

        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        nose.tools.assert_true(resources[0]['name'] in resources[0]['url'])

    @requests_mock.Mocker(real_http=True)
    def test_it_uploads_resources_with_inline_dicts_as_data(self,
                                                            mock_requests):
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
        mock_requests.register_uri('GET', url, json=datapackage)

        helpers.call_action('package_create_from_datapackage', url=url)

        dataset = helpers.call_action('package_show', id='foo')
        resources = dataset.get('resources')

        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        nose.tools.assert_true(resources[0]['name'] in resources[0]['url'])

    @requests_mock.Mocker(real_http=True)
    def test_it_allows_specifying_the_dataset_name(self, mock_requests):
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        mock_requests.register_uri('GET', url, json=datapackage)

        dataset = helpers.call_action('package_create_from_datapackage',
                                      url=url,
                                      name='bar')
        nose.tools.assert_equal(dataset['name'], 'bar')

    @requests_mock.Mocker(real_http=True)
    def test_it_creates_unique_name_if_name_wasnt_specified(self,
                                                            mock_requests):
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        mock_requests.register_uri('GET', url, json=datapackage)

        helpers.call_action('package_create', name=datapackage['name'])
        dataset = helpers.call_action('package_create_from_datapackage',
                                      url=url)
        nose.tools.assert_true(dataset['name'].startswith('foo'))

    @requests_mock.Mocker(real_http=True)
    def test_it_fails_if_specifying_name_that_already_exists(self,
                                                             mock_requests):
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        mock_requests.register_uri('GET', url, json=datapackage)

        helpers.call_action('package_create', name=datapackage['name'])
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_create_from_datapackage',
            url=url,
            name=datapackage['name']
        )

    @requests_mock.Mocker(real_http=True)
    def test_it_allows_changing_dataset_visibility(self, mock_requests):
        url = 'http://www.somewhere.com/datapackage.json'
        datapackage = {
            'name': 'foo',
        }
        mock_requests.register_uri('GET', url, json=datapackage)

        user = factories.Sysadmin()
        organization = factories.Organization()
        dataset = helpers.call_action('package_create_from_datapackage',
                                      context={'user': user['id']},
                                      url=url,
                                      owner_org=organization['id'],
                                      private='true')
        nose.tools.assert_true(dataset['private'])

    def test_it_allows_uploading_a_datapackage(self):
        datapackage = {
            'name': 'foo',
        }
        with tempfile.NamedTemporaryFile() as tmpfile:
            tmpfile.write(json.dumps(datapackage))
            tmpfile.flush()

            dataset = helpers.call_action('package_create_from_datapackage',
                                          upload=_UploadFile(tmpfile))
            nose.tools.assert_equal(dataset['name'], 'foo')


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''

    def __init__(self, fp):
        self.file = fp
