'''Unit tests for lib/sdf.py.

'''
import os.path
import json

import nose.tools

import ckanext.b2.lib.sdf as sdf


def test_convert_to_sdf():
    gold_filepath = os.path.join('../test-data/gold-prices.json')
    gold_filepath = os.path.join(os.path.split(__file__)[0], gold_filepath)
    gold = json.load(open(gold_filepath))

    datapackage = sdf.convert_to_sdf(gold)

    nose.tools.assert_equals(datapackage['name'], 'gold-prices')
    resource = datapackage['resources'][0]
    nose.tools.assert_equals(
        resource['url'],
        'https://raw.github.com/datasets/gold-prices/master/data/data.csv',
    )
    schema = resource['schema']
    expected_schema = {
        u'fields': [
            {u'type': u'string', u'name': u'date'},
            {u'type': u'number', u'name': u'price'}
        ]
    }
    nose.tools.assert_equals(schema, expected_schema)


def test_convert_to_sdf_with_non_json_schema_string():
    '''Test graceful failure with non valid json schema strings.'''

    resource_dict = {
        'name': 'package_name',
        'resources': [
            {'url': 'url', 'schema': 'notvalidjson'},
        ]
    }
    sdf.convert_to_sdf(resource_dict)
