import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions
import ckanext.b2.logic.schema


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

def resource_schema_field_show(context, data_dict):

    data_dict, errors = dictization_functions.validate(data_dict,
        ckanext.b2.logic.schema.resource_schema_field_show_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)

    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': data_dict['resource_id']})
    field = schema['fields'][data_dict['index']]
    return field
