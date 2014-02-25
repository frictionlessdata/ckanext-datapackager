import json

import ckan.plugins.toolkit as toolkit


def _empty_json_table_schema():
    '''Return an empty JSON table schema, as a JSON string.

    :rtype: string

    '''
    return json.dumps({'fields': []})


def resource_schema_show(context, data_dict):
    '''Return the given resource's schema.

    :param resource_id: the ID of the resource whose schema should be returned
    :type resource_id: string

    :returns: the resource's schema
    :rtype: dict

    '''
    # TODO: Validation.

    resource_id = data_dict.pop('resource_id')

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})
    schema = resource_dict.get('schema', _empty_json_table_schema())
    schema = json.loads(schema)
    return schema
