# -*- coding: utf-8 -*-

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
