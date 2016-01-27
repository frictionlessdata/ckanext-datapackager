# -*- coding: utf-8 -*-

import nose.tools
import httpretty

import datapackage
import ckanext.datapackager.tests.helpers as custom_helpers
import ckanext.datapackager.lib.converter as converter


class TestConvertToDict(object):

    def setup(self):
        self.resource_dict = {
            'url': 'http://someplace.com/data.csv'
        }
        self.dataset_dict = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
            'resources': [self.resource_dict],
        }

    def test_basic_dataset_in_setup_is_valid(self):
        converter.dataset_to_datapackage(self.dataset_dict)

    def test_dataset_only_requires_a_name_to_be_valid(self):
        invalid_dataset_dict = {}
        valid_dataset_dict = {
            'name': 'gdp'
        }

        converter.dataset_to_datapackage(valid_dataset_dict)
        nose.tools.assert_raises(
            KeyError,
            converter.dataset_to_datapackage,
            invalid_dataset_dict
        )

    def test_dataset_name_title_and_version(self):
        self.dataset_dict.update({
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result, self.dataset_dict)

    def test_dataset_notes(self):
        self.dataset_dict.update({
            'notes': 'Country, regional and world GDP in current US Dollars.'
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result.get('description'),
                                 self.dataset_dict['notes'])

    def test_dataset_license(self):
        license = {
            'type': 'cc-zero',
            'title': 'Creative Commons CC Zero License (cc-zero)',
            'url': 'http://opendefinition.org/licenses/cc-zero/'
        }
        self.dataset_dict.update({
            'license_id': license['type'],
            'license_title': license['title'],
            'license_url': license['url'],
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result.get('license'), license)

    def test_dataset_author_and_source(self):
        sources = [
            {
                'name': 'World Bank and OECD',
                'email': 'someone@worldbank.org',
                'web': 'http://data.worldbank.org/indicator/NY.GDP.MKTP.CD',
            }
        ]
        self.dataset_dict.update({
            'author': sources[0]['name'],
            'author_email': sources[0]['email'],
            'url': sources[0]['web']
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result.get('sources'), sources)

    def test_dataset_maintainer(self):
        author = {
            'name': 'John Smith',
            'email': 'jsmith@email.com'
        }
        self.dataset_dict.update({
            'maintainer': author['name'],
            'maintainer_email': author['email'],
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result.get('author'), author)

    def test_dataset_tags(self):
        keywords = [
            'economy', 'worldbank'
        ]
        self.dataset_dict.update({
            'tags': [
                {
                    'display_name': 'economy',
                    'id': '9d602a79-7742-44a7-9029-50b9eca38c90',
                    'name': 'economy',
                    'state': 'active'
                },
                {
                    'display_name': 'worldbank',
                    'id': '3ccc2e3b-f875-49ef-a39d-6601d6c0ef76',
                    'name': 'worldbank',
                    'state': 'active'
                }
            ]
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result.get('keywords'), keywords)

    def test_dataset_ckan_url(self):
        self.dataset_dict.update({
            'ckan_url': 'http://www.somewhere.com/datasets/foo'
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equals(result.get('homepage'),
                                 self.dataset_dict['ckan_url'])

    def test_dataset_extras(self):
        self.dataset_dict.update({
            'extras': [
                {'key': 'title_cn', 'value': u'國內生產總值'},
                {'key': 'years', 'value': '[2015, 2016]'},
                {'key': 'last_year', 'value': 2016},
                {'key': 'location', 'value': '{"country": "China"}'},
            ]
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        nose.tools.assert_equal(result.get('extras'), {
            'title_cn': u'國內生產總值',
            'years': [2015, 2016],
            'last_year': 2016,
            'location': {'country': 'China'},
        })

    def test_resource_url(self):
        self.resource_dict.update({
            'url': 'http://www.somewhere.com/data.csv',
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('url'),
                                 self.resource_dict['url'])

    def test_resource_path_isnt_set_even_for_uploaded_resources(self):
        self.resource_dict.update({
            'id': 'foo',
            'url': 'http://www.somewhere.com/data.csv',
            'url_type': 'upload',
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('url'),
                                 self.resource_dict['url'])
        nose.tools.assert_not_in('path', resource)

    def test_resource_description(self):
        self.resource_dict.update({
            'description': 'GDPs list',
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('description'),
                                 self.resource_dict['description'])

    def test_resource_format(self):
        self.resource_dict.update({
            'format': 'CSV',
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('format'),
                                 self.resource_dict['format'])

    def test_resource_hash(self):
        self.resource_dict.update({
            'hash': 'e785c0883d7a104330e69aee73d4f235',
        })
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('hash'),
                                 self.resource_dict['hash'])

    def test_resource_name_lowercases_the_name(self):
        self.resource_dict.update({
            'name': 'ThE-nAmE',
        })
        expected_name = 'the-name'
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('name'),
                                 expected_name)
        nose.tools.assert_equals(resource.get('title'),
                                 self.resource_dict['name'])

    def test_resource_name_slugifies_the_name(self):
        self.resource_dict.update({
            'name': 'Lista de PIBs dos países!   51',
        })
        expected_name = 'lista-de-pibs-dos-paises-51'
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('name'),
                                 expected_name)
        nose.tools.assert_equals(resource.get('title'),
                                 self.resource_dict['name'])

    def test_resource_name_converts_unicode_characters(self):
        self.resource_dict.update({
            'name': u'万事开头难',
        })
        expected_name = 'mo-shi-kai-tou-nan'
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('name'),
                                 expected_name)
        nose.tools.assert_equals(resource.get('title'),
                                 self.resource_dict['name'])


class TestDataPackageToDatasetDict(object):
    def setup(self):
        datapackage_dict = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
            'resources': [
                {'path': custom_helpers.fixture_path('datetimes.csv')}
            ],
        }

        self.datapackage = datapackage.DataPackage(datapackage_dict)

    def test_basic_datapackage_in_setup_is_valid(self):
        converter.datapackage_to_dataset(self.datapackage)

    def test_datapackage_only_requires_a_name_to_be_valid(self):
        invalid_datapackage = datapackage.DataPackage({})
        valid_datapackage = datapackage.DataPackage({
            'name': 'gdp'
        })

        converter.datapackage_to_dataset(valid_datapackage)
        nose.tools.assert_raises(
            KeyError,
            converter.datapackage_to_dataset,
            invalid_datapackage
        )

    def test_datapackage_name_title_and_version(self):
        self.datapackage.metadata.update({
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        datapackage_dict = self.datapackage.to_dict()
        nose.tools.assert_equals(result['name'], datapackage_dict['name'])
        nose.tools.assert_equals(result['title'], datapackage_dict['title'])
        nose.tools.assert_equals(result['version'],
                                 datapackage_dict['version'])

    def test_name_is_lowercased(self):
        self.datapackage.metadata.update({
            'name': 'ThEnAmE',
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result['name'],
                                 self.datapackage.metadata['name'].lower())

    def test_datapackage_description(self):
        self.datapackage.metadata.update({
            'description': 'Country, regional and world GDP in current USD.'
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('notes'),
                                 self.datapackage.metadata['description'])

    def test_datapackage_license_as_string(self):
        self.datapackage.metadata.update({
            'license': 'cc-zero'
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('license_id'), 'cc-zero')

    def test_datapackage_license_as_unicode(self):
        self.datapackage.metadata.update({
            'license': u'cc-zero'
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('license_id'), 'cc-zero')

    def test_datapackage_license_as_dict(self):
        license = {
            'type': 'cc-zero',
            'title': 'Creative Commons CC Zero License (cc-zero)',
            'url': 'http://opendefinition.org/licenses/cc-zero/'
        }
        self.datapackage.metadata.update({
            'license': license
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('license_id'), license['type'])
        nose.tools.assert_equals(result.get('license_title'), license['title'])
        nose.tools.assert_equals(result.get('license_url'), license['url'])

    def test_datapackage_sources(self):
        sources = [
            {
                'name': 'World Bank and OECD',
                'email': 'someone@worldbank.org',
                'web': 'http://data.worldbank.org/indicator/NY.GDP.MKTP.CD',
            }
        ]
        self.datapackage.metadata.update({
            'sources': sources
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('author'), sources[0]['name'])
        nose.tools.assert_equals(result.get('author_email'),
                                 sources[0]['email'])
        nose.tools.assert_equals(result.get('url'), sources[0]['web'])

    def test_datapackage_author_as_string(self):
        # FIXME: Add author.web
        author = {
            'name': 'John Smith',
            'email': 'jsmith@email.com'
        }
        self.datapackage.metadata.update({
            'author': '{name} <{email}>'.format(name=author['name'],
                                                email=author['email'])
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('maintainer'), author['name'])
        nose.tools.assert_equals(result.get('maintainer_email'),
                                 author['email'])

    def test_datapackage_author_as_unicode(self):
        # FIXME: Add author.web
        author = {
            'name': u'John Smith',
        }
        self.datapackage.metadata.update({
            'author': author['name'],
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('maintainer'), author['name'])

    def test_datapackage_author_as_string_without_email(self):
        # FIXME: Add author.web
        author = {
            'name': 'John Smith'
        }
        self.datapackage.metadata.update({
            'author': author['name']
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('maintainer'), author['name'])

    def test_datapackage_author_as_dict(self):
        # FIXME: Add author.web
        author = {
            'name': 'John Smith',
            'email': 'jsmith@email.com'
        }
        self.datapackage.metadata.update({
            'author': author
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('maintainer'), author['name'])
        nose.tools.assert_equals(result.get('maintainer_email'),
                                 author['email'])

    def test_datapackage_keywords(self):
        keywords = [
            'economy!!!', 'world bank',
        ]
        self.datapackage.metadata.update({
            'keywords': keywords
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('tags'), [
            {'name': 'economy'},
            {'name': 'world-bank'},
        ])

    def test_datapackage_extras(self):
        self.datapackage.metadata.update({
            'title_cn': u'國內生產總值',
            'years': [2015, 2016],
            'last_year': 2016,
            'location': {'country': 'China'},
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_items_equal(result.get('extras'), [
            {'key': 'title_cn', 'value': u'國內生產總值'},
            {'key': 'years', 'value': '[2015, 2016]'},
            {'key': 'last_year', 'value': 2016},
            {'key': 'location', 'value': '{"country": "China"}'},
        ])

    def test_resource_name_is_used_if_theres_no_title(self):
        resource = {
            'name': 'gdp',
            'title': None,
        }
        self.datapackage.metadata.update({
            'resources': [resource],
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(result.get('resources')[0].get('name'),
                                 resource['name'])

    def test_resource_title_is_used_as_name(self):
        resource = {
            'name': 'gdp',
            'title': 'Gross domestic product',
        }
        self.datapackage.metadata.update({
            'resources': [resource],
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('resources')[0].get('name'),
                                 resource['title'])

    @httpretty.activate
    def test_resource_url(self):
        url = 'http://www.somewhere.com/data.csv'
        resource = {
            'url': url
        }
        httpretty.register_uri(httpretty.GET, url, body='')
        self.datapackage.metadata.update({
            'resources': [resource]
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('resources')[0].get('url'),
                                 resource['url'])

    @httpretty.activate
    def test_resource_url_is_set_to_its_remote_data_path(self):
        url = 'http://www.somewhere.com/data.csv'
        datapackage_dict = {
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
            'resources': [
                {'path': 'data.csv'}
            ],
            'base': 'http://www.somewhere.com',
        }
        httpretty.register_uri(httpretty.GET, url, body='')
        dp = datapackage.DataPackage(datapackage_dict)
        result = converter.datapackage_to_dataset(dp)
        nose.tools.assert_equals(result.get('resources')[0].get('url'),
                                 dp.resources[0].remote_data_path)

    def test_resource_description(self):
        resource = {
            'description': 'GDPs list'
        }
        self.datapackage.metadata.update({
            'resources': [resource]
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('resources')[0].get('description'),
                                 resource['description'])

    def test_resource_format(self):
        resource = {
            'format': 'CSV',
        }
        self.datapackage.metadata.update({
            'resources': [resource]
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('resources')[0].get('format'),
                                 resource['format'])

    def test_resource_hash(self):
        resource = {
            'hash': 'e785c0883d7a104330e69aee73d4f235',
        }
        self.datapackage.metadata.update({
            'resources': [resource]
        })
        result = converter.datapackage_to_dataset(self.datapackage)
        nose.tools.assert_equals(result.get('resources')[0].get('hash'),
                                 resource['hash'])

    def test_resource_path_is_set_to_its_local_data_path(self):
        resource = {
            'path': custom_helpers.fixture_path('datetimes.csv'),
        }
        dp = datapackage.DataPackage({
            'name': 'datetimes',
            'resources': [resource],
        })

        result = converter.datapackage_to_dataset(dp)
        nose.tools.assert_equals(result.get('resources')[0].get('path'),
                                 dp.resources[0].local_data_path)
