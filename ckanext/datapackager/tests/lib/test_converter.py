# -*- coding: utf-8 -*-

import unittest
import pytest
import responses

from frictionless_ckan_mapper import frictionless_to_ckan as f2c
from frictionless_ckan_mapper import ckan_to_frictionless as converter
import datapackage

class TestConvertToDict(unittest.TestCase, object):
    def setUp(self):
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
        converter.dataset(self.dataset_dict)

    # TODO: Check if a exception must be raised for an empty dataset dict
    #def test_dataset_only_requires_a_name_to_be_valid(self):
    #    invalid_dataset_dict = {}
    #    valid_dataset_dict = {
    #        "name": "gdp",
    #        "resources": [
    #            {
    #                "name": "the-resource",
    #            }
    #        ],
    #    }

    #    converter.dataset(valid_dataset_dict)
    #    with self.assertRaises(KeyError):
    #        converter.dataset(invalid_dataset_dict)

    def test_dataset_name_title_and_version(self):
        self.dataset_dict.update(
            {
                "name": "gdp",
                "title": "Countries GDP",
                "version": "1.0",
            }
        )
        result = converter.dataset(self.dataset_dict)
        assert result["title"] == self.dataset_dict["title"]
        assert result["name"] == self.dataset_dict["name"]
        assert result["version"] == self.dataset_dict["version"]

    def test_dataset_notes(self):
        self.dataset_dict.update(
            {"notes": "Country, regional and world GDP in current US Dollars."}
        )
        result = converter.dataset(self.dataset_dict)
        assert result.get("description") == self.dataset_dict["notes"]

    def test_dataset_license(self):
        license = {
            "name": "cc-zero",
            "title": "Creative Commons CC Zero License (cc-zero)",
            "path": "http://opendefinition.org/licenses/cc-zero/",
        }
        self.dataset_dict.update(
            {
                "license_id": license["name"],
                "license_title": license["title"],
                "license_url": license["path"],
            }
        )
        result = converter.dataset(self.dataset_dict)
        assert result.get("licenses")[0] == license

    # TODO: check if it needs to get the author and add as the datapackage source
    #def test_dataset_author_and_source(self):
    #    sources = [
    #        {
    #            "name": "World Bank and OECD",
    #            "email": "someone@worldbank.org",
    #            "web": "http://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
    #        }
    #    ]
    #    self.dataset_dict.update(
    #        {
    #            "author": sources[0]["name"],
    #            "author_email": sources[0]["email"],
    #            "url": sources[0]["web"],
    #        }
    #    )
    #    result = converter.dataset(self.dataset_dict)
    #    assert result.get("sources") == sources

    def test_dataset_maintainer(self):
        author = {"title": "John Smith", "email": "jsmith@email.com", "role": "maintainer"}
        self.dataset_dict.update(
            {
                "maintainer": author["title"],
                "maintainer_email": author["email"],
            }
        )
        result = converter.dataset(self.dataset_dict)
        assert result.get("contributors")[0] == author

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
        result = converter.dataset(self.dataset_dict)
        assert result.get("keywords") == keywords

    # TODO: check how ckan_url must be transformed
    #def test_dataset_ckan_url(self):
    #    self.dataset_dict.update({"ckan_url": "http://www.somewhere.com/datasets/foo"})
    #    result = converter.dataset(self.dataset_dict)
    #    assert result.get("homepage") == self.dataset_dict["ckan_url"]

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
        result = converter.dataset(self.dataset_dict)
        assert result.get("title_cn") == "國內生產總值"
        assert result.get("years") == [2015, 2016]
        assert result.get("last_year") == 2016
        assert result.get("location") == {"country": "China"}

    def test_resource_url(self):
        self.resource_dict.update(
            {
                "url": "http://www.somewhere.com/data.csv",
            }
        )
        result = converter.dataset(self.dataset_dict)
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
        result = converter.dataset(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("path") == self.resource_dict["url"]

    def test_resource_description(self):
        self.resource_dict.update(
            {
                "description": "GDPs list",
            }
        )
        result = converter.dataset(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("description") == self.resource_dict["description"]

    def test_resource_format(self):
        self.resource_dict.update(
            {
                "format": "CSV",
            }
        )
        result = converter.dataset(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("format") == self.resource_dict["format"]

    def test_resource_hash(self):
        self.resource_dict.update(
            {
                "hash": "e785c0883d7a104330e69aee73d4f235",
            }
        )
        result = converter.dataset(self.dataset_dict)
        resource = result.get("resources")[0]
        assert resource.get("hash") == self.resource_dict["hash"]

    # TODO: See https://github.com/frictionlessdata/frictionless-ckan-mapper/issues/48
    #def test_resource_name_lowercases_the_name(self):
    #    self.resource_dict.update(
    #        {
    #            "name": "ThE-nAmE",
    #        }
    #    )
    #    expected_name = "the-name"
    #    result = converter.dataset(self.dataset_dict)
    #    resource = result.get("resources")[0]
    #    assert resource.get("name") == expected_name
    #    assert resource.get("title") == self.resource_dict["name"]

    # TODO: See https://github.com/frictionlessdata/frictionless-ckan-mapper/issues/48
    #def test_resource_name_slugifies_the_name(self):
    #    self.resource_dict.update(
    #        {
    #            "name": "Lista de PIBs dos países!   51",
    #        }
    #    )
    #    expected_name = "lista-de-pibs-dos-paises-51"
    #    result = converter.dataset(self.dataset_dict)
    #    resource = result.get("resources")[0]
    #    assert resource.get("name") == expected_name
    #    assert resource.get("title") == self.resource_dict["name"]

    # TODO: See https://github.com/frictionlessdata/frictionless-ckan-mapper/issues/48
    #def test_resource_name_converts_unicode_characters(self):
    #    self.resource_dict.update(
    #        {
    #            "name": u"万事开头难",
    #        }
    #    )
    #    expected_name = "mo-shi-kai-tou-nan"
    #    result = converter.dataset(self.dataset_dict)
    #    resource = result.get("resources")[0]
    #    assert resource.get("name") == expected_name
    #    assert resource.get("title") == self.resource_dict["name"]


class TestDataPackageToDatasetDict(unittest.TestCase, object):
    def setUp(self):
        datapackage_dict = {
            "name": "gdp",
            "title": "Countries GDP",
            "version": "1.0",
            "resources": [{"name": "datetimes.csv", "path": "test-data/datetimes.csv"}],
        }

        self.datapackage = f2c.package(datapackage_dict)

    def test_basic_datapackage_in_setup_is_valid(self):
        f2c.package(self.datapackage)

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

        f2c.package(valid_datapackage.to_dict())

        with pytest.raises(TypeError):
            converter.dataset(invalid_datapackage)

    def test_datapackage_name_title_and_version(self):
        self.datapackage.update(
            {
                "name": "gdp",
                "title": "Countries GDP",
                "version": "1.0",
            }
        )
        result = f2c.package(self.datapackage)
        datapackage_dict = self.datapackage
        assert result["name"] == datapackage_dict["name"]
        assert result["title"] == datapackage_dict["title"]
        assert result["version"] == datapackage_dict["version"]
    
    # TODO: check if the name must be lowercased on frictionless-ckan-mapper
    #def test_name_is_lowercased(self):
    #    self.datapackage.update(
    #        {
    #            "name": "ThEnAmE",
    #        }
    #    )
    #    result = f2c.package(self.datapackage)
    #    assert result["name"] == self.datapackage["name"].lower()

    def test_datapackage_description(self):
        self.datapackage.update(
            {"description": "Country, regional and world GDP in current USD."}
        )
        result = f2c.package(self.datapackage)
        assert result.get("notes") == self.datapackage["description"]

    # TODO: confirm that the folowing tests don't make sense according to the latest Datapackage spec
    #def test_datapackage_license_as_string(self):
    #    self.datapackage.update({"license": [{"name": "cc-zero"}]})
    #    result = f2c.package(self.datapackage)
    #    assert result.get("license_id") == "cc-zero"

    #def test_datapackage_license_as_unicode(self):
    #    self.datapackage.update({"licenses": [{"name": "cc-zero"}]})
    #    result = f2c.package(self.datapackage)
    #    assert result.get("license_id") == "cc-zero"

    def test_datapackage_license_as_dict(self):
        license = {
            "name": "cc-zero",
            "title": "Creative Commons CC Zero License (cc-zero)",
            "path": "http://opendefinition.org/licenses/cc-zero/",
        }
        self.datapackage.update({"licenses": [license]})
        result = f2c.package(self.datapackage)
        assert result.get("license_id") == license["name"]
        assert result.get("license_title") == license["title"]
        assert result.get("license_url") == license["path"]

    # TODO: Check if this is the expected behaviour for sources
    #def test_datapackage_sources(self):
    #    sources = [
    #        {
    #            "name": "World Bank and OECD",
    #            "email": "someone@worldbank.org",
    #            "web": "http://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
    #        }
    #    ]
    #    self.datapackage.update({"sources": sources})
    #    result = f2c.package(self.datapackage)
    #    assert result.get("author") == sources[0]["name"]
    #    assert result.get("author_email") == sources[0]["email"]
    #    assert result.get("url") == sources[0]["web"]

    # TODO: Check how author email is written in CKAN
    def test_datapackage_author_as_string(self):
        # FIXME: Add author.web
        author = {"name": "John Smith", "email": "jsmith@email.com"}
        self.datapackage.update({
            'contributors': [{
                "title": author["name"], 
                "email": author["email"],
                "role": "author"
            }]
        })
        result = f2c.package(self.datapackage)

        assert result.get("author") == author["name"]
        assert result.get("author_email") == author["email"]

    def test_datapackage_author_as_unicode(self):
        # FIXME: Add author.web
        author = {
            "name": u"John Smith",
        }
        self.datapackage.update(
            {
                "author": author["name"],
            }
        )
        result = f2c.package(self.datapackage)
        assert result.get("author") == author["name"]

    def test_datapackage_author_as_string_without_email(self):
        # FIXME: Add author.web
        author = {"name": "John Smith"}
        self.datapackage.update({"author": author["name"]})
        result = f2c.package(self.datapackage)
        assert result.get("author") == author["name"]

    def test_datapackage_author_as_dict(self):
        # FIXME: Add author.web
        author = {"title": "John Smith", "email": "jsmith@email.com", "role": "author"}
        self.datapackage.update({
            "contributors": [author]
        })
        result = f2c.package(self.datapackage)
        assert result.get("author") == author["title"]
        assert result.get("author_email") == author["email"]

    # TODO: Check if the tag convertion to CKAN is valid
    def test_datapackage_keywords(self):
        keywords = [
            "economy!!!",
            "world bank",
        ]
        self.datapackage.update({"keywords": keywords})
        result = f2c.package(self.datapackage)
        result_tags = [ t["name"] for t in result.get("tags") ]
        assert "economy!!!" in result_tags
        assert "world bank" in result_tags

    def test_datapackage_extras(self):
        self.datapackage.update(
            {
                "title_cn": u"國內生產總值",
                "years": [2015, 2016],
                "last_year": 2016,
                "location": {"country": "China"},
            }
        )
        result = f2c.package(self.datapackage)
        assert sorted(result.get('extras'), key=lambda e: e["key"]) == [
            {'key': 'last_year', 'value': 2016},
            {'key': 'location', 'value': '{"country": "China"}'},
            {'key': 'title_cn', 'value': u'國內生產總值'},
            {'key': 'years', 'value': '[2015, 2016]'},
        ]

    def test_resource_name_is_used_if_theres_no_title(self):
        resource = {
            "name": "gdp",
            "title": None,
        }
        self.datapackage['resources'][0].update(resource)
        result = f2c.package(self.datapackage)
        resource = result.get("resources")[0]
        assert result.get("resources")[0].get("name") == resource["name"]

    # TODO: check if the following test makes sense
    #def test_resource_title_is_used_as_name(self):
    #    resource = {
    #        "name": "gdp",
    #        "title": "Gross domestic product",
    #    }

    #    self.datapackage['resources'][0].update(resource)
    #    result = f2c.package(self.datapackage)
    #    assert result.get("resources")[0].get("name") == resource["title"]

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

        dp = datapackage.DataPackage(datapackage_dict).to_dict()
        result = f2c.package(dp)
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
        responses.add(responses.GET, url, body="")
        dp = datapackage.DataPackage(
            datapackage_dict, base_path="http://www.somewhere.com"
        ).to_dict()
        result = f2c.package(dp)
        assert result.get("resources")[0].get("url") == dp['resources'][0]['path']

    def test_resource_description(self):
        resource = {"description": "GDPs list"}

        self.datapackage['resources'][0].update(resource)
        result = f2c.package(self.datapackage)
        assert result.get("resources")[0].get("description") == resource["description"]

    def test_resource_format(self):
        resource = {
            "format": "CSV",
        }

        self.datapackage['resources'][0].update(resource)
        result = f2c.package(self.datapackage)
        assert result.get("resources")[0].get("format") == resource["format"]

    def test_resource_hash(self):
        resource = {
            "hash": "e785c0883d7a104330e69aee73d4f235",
        }

        self.datapackage['resources'][0].update(resource)
        result = f2c.package(self.datapackage)
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
        ).to_dict()

        result = f2c.package(dp)
        assert result.get("resources")[0].get("url") == dp['resources'][0]['path']
