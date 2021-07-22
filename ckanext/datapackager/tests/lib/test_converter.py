# -*- coding: utf-8 -*-

import unittest
import responses

from ckan_datapackage_tools import converter
import datapackage

class TestConvertToDict(unittest.TestCase, object):
    def setup(self):
        self.resource_dict = {
            "id": "1234",
            "name": "data.csv",
            "url": "http://someplace.com/data.csv",
        }
        self.dataset_dict = {
            "name": "gdp",
            "title": "Countries GDP",
            "version": "1.0",
            "resources": [self.resource_dict],
        }

    def test_basic_dataset_in_setup_is_valid(self):
        converter.dataset_to_datapackage(self.dataset_dict)

    def test_dataset_only_requires_a_name_to_be_valid(self):
        invalid_dataset_dict = {}
        valid_dataset_dict = {
            "name": "gdp",
            "resources": [
                {
                    "name": "the-resource",
                }
            ],
        }

        converter.dataset_to_datapackage(valid_dataset_dict)
        with self.assertRaises(KeyError):
            converter.dataset_to_datapackage(invalid_dataset_dict)

    def test_dataset_name_title_and_version(self):
        self.dataset_dict.update(
            {
                "name": "gdp",
                "title": "Countries GDP",
                "version": "1.0",
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result["title"] == self.dataset_dict["title"]
        assert result["name"] == self.dataset_dict["name"]
        assert result["version"] == self.dataset_dict["version"]

    def test_dataset_notes(self):
        self.dataset_dict.update(
            {"notes": "Country, regional and world GDP in current US Dollars."}
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("description") == self.dataset_dict["notes"]

    def test_dataset_license(self):
        license = {
            "type": "cc-zero",
            "title": "Creative Commons CC Zero License (cc-zero)",
            "url": "http://opendefinition.org/licenses/cc-zero/",
        }
        self.dataset_dict.update(
            {
                "license_id": license["type"],
                "license_title": license["title"],
                "license_url": license["url"],
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("license") == license

    def test_dataset_author_and_source(self):
        sources = [
            {
                "name": "World Bank and OECD",
                "email": "someone@worldbank.org",
                "web": "http://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
            }
        ]
        self.dataset_dict.update(
            {
                "author": sources[0]["name"],
                "author_email": sources[0]["email"],
                "url": sources[0]["web"],
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("sources") == sources

    def test_dataset_maintainer(self):
        author = {"name": "John Smith", "email": "jsmith@email.com"}
        self.dataset_dict.update(
            {
                "maintainer": author["name"],
                "maintainer_email": author["email"],
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("author") == author

    def test_dataset_tags(self):
        keywords = ["economy", "worldbank"]
        self.dataset_dict.update(
            {
                "tags": [
                    {
                        "display_name": "economy",
                        "id": "9d602a79-7742-44a7-9029-50b9eca38c90",
                        "name": "economy",
                        "state": "active",
                    },
                    {
                        "display_name": "worldbank",
                        "id": "3ccc2e3b-f875-49ef-a39d-6601d6c0ef76",
                        "name": "worldbank",
                        "state": "active",
                    },
                ]
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("keywords") == keywords

    def test_dataset_ckan_url(self):
        self.dataset_dict.update({"ckan_url": "http://www.somewhere.com/datasets/foo"})
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("homepage") == self.dataset_dict["ckan_url"]

    def test_dataset_extras(self):
        self.dataset_dict.update(
            {
                "extras": [
                    {"key": "title_cn", "value": u"國內生產總值"},
                    {"key": "years", "value": "[2015, 2016]"},
                    {"key": "last_year", "value": 2016},
                    {"key": "location", "value": '{"country": "China"}'},
                ]
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        assert result.get("extras") == {
            "title_cn": u"國內生產總值",
            "years": [2015, 2016],
            "last_year": 2016,
            "location": {"country": "China"},
        }

    def test_resource_url(self):
        self.resource_dict.update(
            {
                "url": "http://www.somewhere.com/data.csv",
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("path") == self.resource_dict["url"]

    def test_resource_path_is_set_even_for_uploaded_resources(self):
        self.resource_dict.update(
            {
                "id": "foo",
                "url": "http://www.somewhere.com/data.csv",
                "url_type": "upload",
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("path") == self.resource_dict["url"]

    def test_resource_description(self):
        self.resource_dict.update(
            {
                "description": "GDPs list",
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("description") == self.resource_dict["description"]

    def test_resource_format(self):
        self.resource_dict.update(
            {
                "format": "CSV",
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("format") == self.resource_dict["format"]

    def test_resource_hash(self):
        self.resource_dict.update(
            {
                "hash": "e785c0883d7a104330e69aee73d4f235",
            }
        )
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("hash") == self.resource_dict["hash"]

    def test_resource_name_lowercases_the_name(self):
        self.resource_dict.update(
            {
                "name": "ThE-nAmE",
            }
        )
        expected_name = "the-name"
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("name") == expected_name
        assert resource.get("title") == self.resource_dict["name"]

    def test_resource_name_slugifies_the_name(self):
        self.resource_dict.update(
            {
                "name": "Lista de PIBs dos países!   51",
            }
        )
        expected_name = "lista-de-pibs-dos-paises-51"
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("name") == expected_name
        assert resource.get("title") == self.resource_dict["name"]

    def test_resource_name_converts_unicode_characters(self):
        self.resource_dict.update(
            {
                "name": u"万事开头难",
            }
        )
        expected_name = "mo-shi-kai-tou-nan"
        result = converter.dataset_to_datapackage(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("name") == expected_name
        assert resource.get("title") == self.resource_dict["name"]


class TestDataPackageToDatasetDict(unittest.TestCase, object):
    def setup(self):
        datapackage_dict = {
            "name": "gdp",
            "title": "Countries GDP",
            "version": "1.0",
            "resources": [{"name": "datetimes.csv", "path": "test-data/datetimes.csv"}],
        }

        self.datapackage = datapackage.DataPackage(datapackage_dict)

    def test_basic_datapackage_in_setup_is_valid(self):
        converter.datapackage_to_dataset(self.datapackage)

    def test_datapackage_only_requires_some_fields_to_be_valid(self):
        invalid_datapackage = datapackage.DataPackage({})
        valid_datapackage = datapackage.DataPackage(
            {
                "name": "gdp",
                "resources": [
                    {"name": "the-resource", "path": "http://example.com/some-data.csv"}
                ],
            }
        )

        converter.datapackage_to_dataset(valid_datapackage)
        with self.assertRaises(KeyError):
            converter.dataset_to_datapackage(invalid_datapackage)

    def test_datapackage_name_title_and_version(self):
        self.datapackage.descriptor.update(
            {
                "name": "gdp",
                "title": "Countries GDP",
                "version": "1.0",
            }
        )
        result = converter.datapackage_to_dataset(self.datapackage)
        datapackage_dict = self.datapackage.to_dict()
        assert result["name"] == datapackage_dict["name"]
        assert result["title"] == datapackage_dict["title"]
        assert result["version"] == datapackage_dict["version"]

    def test_name_is_lowercased(self):
        self.datapackage.descriptor.update(
            {
                "name": "ThEnAmE",
            }
        )
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result["name"] == self.datapackage.descriptor["name"].lower()

    def test_datapackage_description(self):
        self.datapackage.descriptor.update(
            {"description": "Country, regional and world GDP in current USD."}
        )
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("notes") == self.datapackage.descriptor["description"]

    def test_datapackage_license_as_string(self):
        self.datapackage.descriptor.update({"license": "cc-zero"})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("license_id") == "cc-zero"

    def test_datapackage_license_as_unicode(self):
        self.datapackage.descriptor.update({"license": u"cc-zero"})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("license_id") == "cc-zero"

    def test_datapackage_license_as_dict(self):
        license = {
            "type": "cc-zero",
            "title": "Creative Commons CC Zero License (cc-zero)",
            "url": "http://opendefinition.org/licenses/cc-zero/",
        }
        self.datapackage.descriptor.update({"license": license})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("license_id") == license["type"]
        assert result.get("license_title") == license["title"]
        assert result.get("license_url") == license["url"]

    def test_datapackage_sources(self):
        sources = [
            {
                "name": "World Bank and OECD",
                "email": "someone@worldbank.org",
                "web": "http://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
            }
        ]
        self.datapackage.descriptor.update({"sources": sources})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("author") == sources[0]["name"]
        assert result.get("author_email") == sources[0]["email"]
        assert result.get("url") == sources[0]["web"]

    def test_datapackage_author_as_string(self):
        # FIXME: Add author.web
        author = {"name": "John Smith", "email": "jsmith@email.com"}
        self.datapackage.descriptor.update(
            {
                "author": "{name} <{email}>".format(
                    name=author["name"], email=author["email"]
                )
            }
        )
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("maintainer") == author["name"]
        assert result.get("maintainer_email") == author["email"]

    def test_datapackage_author_as_unicode(self):
        # FIXME: Add author.web
        author = {
            "name": u"John Smith",
        }
        self.datapackage.descriptor.update(
            {
                "author": author["name"],
            }
        )
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("maintainer") == author["name"]

    def test_datapackage_author_as_string_without_email(self):
        # FIXME: Add author.web
        author = {"name": "John Smith"}
        self.datapackage.descriptor.update({"author": author["name"]})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("maintainer") == author["name"]

    def test_datapackage_author_as_dict(self):
        # FIXME: Add author.web
        author = {"name": "John Smith", "email": "jsmith@email.com"}
        self.datapackage.descriptor.update({"author": author})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("maintainer") == author["name"]
        assert result.get("maintainer_email") == author["email"]

    def test_datapackage_keywords(self):
        keywords = [
            "economy!!!",
            "world bank",
        ]
        self.datapackage.descriptor.update({"keywords": keywords})
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("tags") == [
                {"name": "economy"},
                {"name": "world-bank"},
            ]

    def test_datapackage_extras(self):
        self.datapackage.descriptor.update(
            {
                "title_cn": u"國內生產總值",
                "years": [2015, 2016],
                "last_year": 2016,
                "location": {"country": "China"},
            }
        )
        result = converter.datapackage_to_dataset(self.datapackage)
        self.assertItemsEqual(
            result.get("extras"),
            [
                {"key": "profile", "value": u"data-package"},
                {"key": "title_cn", "value": u"國內生產總值"},
                {"key": "years", "value": "[2015, 2016]"},
                {"key": "last_year", "value": 2016},
                {"key": "location", "value": '{"country": "China"}'},
            ],
        )

    def test_resource_name_is_used_if_theres_no_title(self):
        resource = {
            "name": "gdp",
            "title": None,
        }
        self.datapackage.resources[0].descriptor.update(resource)
        result = converter.datapackage_to_dataset(self.datapackage)
        resource = result.get("resources")[0]
        assert result.get("resources")[0].get("name") == resource["name"]

    def test_resource_title_is_used_as_name(self):
        resource = {
            "name": "gdp",
            "title": "Gross domestic product",
        }

        self.datapackage.resources[0].descriptor.update(resource)
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("resources")[0].get("name") == resource["title"]

    @responses.activate
    def test_resource_url(self):
        url = "http://www.somewhere.com/data.csv"
        datapackage_dict = {
            "name": "gdp",
            "title": "Countries GDP",
            "version": "1.0",
            "resources": [{"path": url}],
        }
        responses.add(responses.GET, url, body='')

        dp = datapackage.DataPackage(datapackage_dict)
        result = converter.datapackage_to_dataset(dp)
        assert (
            result.get("resources")[0].get("url")
            == datapackage_dict["resources"][0]["path"]
        )

    @responses.activate
    def test_resource_url_is_set_to_its_remote_data_path(self):
        url = "http://www.somewhere.com/data.csv"
        datapackage_dict = {
            "name": "gdp",
            "title": "Countries GDP",
            "version": "1.0",
            "resources": [{"path": "data.csv"}],
        }

        responses.add(responses.GET, url, body='')
        dp = datapackage.DataPackage(
            datapackage_dict, base_path="http://www.somewhere.com"
        )
        result = converter.datapackage_to_dataset(dp)
        assert result.get("resources")[0].get("url") == dp.resources[0].source

    def test_resource_description(self):
        resource = {"description": "GDPs list"}

        self.datapackage.resources[0].descriptor.update(resource)
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("resources")[0].get("description") == resource["description"]

    def test_resource_format(self):
        resource = {
            "format": "CSV",
        }

        self.datapackage.resources[0].descriptor.update(resource)
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("resources")[0].get("format") == resource["format"]

    def test_resource_hash(self):
        resource = {
            "hash": "e785c0883d7a104330e69aee73d4f235",
        }

        self.datapackage.resources[0].descriptor.update(resource)
        result = converter.datapackage_to_dataset(self.datapackage)
        assert result.get("resources")[0].get("hash") == resource["hash"]

    def test_resource_path_is_set_to_its_local_data_path(self):
        resource = {
            "path": "test-data/datetimes.csv",
        }
        dp = datapackage.DataPackage(
            {
                "name": "datetimes",
                "resources": [resource],
            }
        )

        result = converter.datapackage_to_dataset(dp)
        assert result.get("resources")[0].get("path") == dp.resources[0].source
