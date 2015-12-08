# -*- coding: utf-8 -*-

import mock
import tempfile
import zipfile
import nose.tools

import ckanext.datapackager.lib.tdf as tdf


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
        tdf.convert_to_tdf(self.dataset_dict)

    def test_dataset_only_requires_a_name_to_be_valid(self):
        invalid_dataset_dict = {}
        valid_dataset_dict = {
            'name': 'gdp'
        }

        tdf.convert_to_tdf(valid_dataset_dict)
        nose.tools.assert_raises(
            KeyError,
            tdf.convert_to_tdf,
            invalid_dataset_dict
        )

    def test_dataset_name_title_and_version(self):
        self.dataset_dict.update({
            'name': 'gdp',
            'title': 'Countries GDP',
            'version': '1.0',
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        nose.tools.assert_equals(result, self.dataset_dict)

    def test_dataset_notes(self):
        self.dataset_dict.update({
            'notes': 'Country, regional and world GDP in current US Dollars.'
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
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
        result = tdf.convert_to_tdf(self.dataset_dict)
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
            'source': sources[0]['web']
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
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
        result = tdf.convert_to_tdf(self.dataset_dict)
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
        result = tdf.convert_to_tdf(self.dataset_dict)
        nose.tools.assert_equals(result.get('keywords'), keywords)

    def test_dataset_extras(self):
        self.dataset_dict.update({
            'extras': [
                {'key': 'title_cn', 'value': u'國內生產總值'},
                {'key': 'last_updated', 'value': '2011-09-21'},
            ]
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        nose.tools.assert_equals(result.get('extras'), {
            'title_cn': u'國內生產總值',
            'last_updated': '2011-09-21',
        })

    def test_resource_url(self):
        self.resource_dict.update({
            'url': 'http://www.somewhere.com/data.csv',
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('url'),
                                 self.resource_dict['url'])

    @mock.patch('ckanext.datapackager.lib.tdf.util')
    def test_resource_path_for_uploaded_files(self, util_mock):
        util_mock.get_path_to_resource_file.return_value = 'the_file_path'
        self.resource_dict.update({
            'id': 'foo',
            'url': 'http://www.somewhere.com/data.csv',
            'url_type': 'upload',
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('url'),
                                 self.resource_dict['url'])
        nose.tools.assert_equals(resource.get('path'),
                                 'the_file_path')

    def test_resource_description(self):
        self.resource_dict.update({
            'description': 'GDPs list',
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('description'),
                                 self.resource_dict['description'])

    def test_resource_format(self):
        self.resource_dict.update({
            'format': 'CSV',
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('format'),
                                 self.resource_dict['format'])

    def test_resource_hash(self):
        self.resource_dict.update({
            'hash': 'e785c0883d7a104330e69aee73d4f235',
        })
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('hash'),
                                 self.resource_dict['hash'])

    def test_resource_name_slugifies_the_name(self):
        self.resource_dict.update({
            'name': 'Lista de PIBs dos países!   51',
        })
        expected_name = 'lista-de-pibs-dos-paises-51'
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('name'),
                                 expected_name)

    def test_resource_name_converts_unicode_characters(self):
        self.resource_dict.update({
            'name': u'万事开头难',
        })
        expected_name = 'mo-shi-kai-tou-nan'
        result = tdf.convert_to_tdf(self.dataset_dict)
        resource = result.get('resources')[0]
        nose.tools.assert_equals(resource.get('name'),
                                 expected_name)


class TestConvertToZip(object):
    def test_writes_the_datapackage_zipfile_to_the_received_file(self):
        dataset_dict = {
            'name': 'foo'
        }
        with tempfile.TemporaryFile() as f:
            tdf.convert_to_tdf_zip(dataset_dict, f)
            with zipfile.ZipFile(f) as z:
                nose.tools.assert_equals(z.namelist(),
                                         ['datapackage.json'])

    def test_accepts_a_file_path(self):
        dataset_dict = {
            'name': 'foo'
        }
        with tempfile.NamedTemporaryFile() as f:
            tdf.convert_to_tdf_zip(dataset_dict, f.name)
            with zipfile.ZipFile(f) as z:
                nose.tools.assert_equals(z.namelist(),
                                         ['datapackage.json'])
