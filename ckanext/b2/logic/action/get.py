import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.b2.logic.schema
import ckanext.b2.exceptions as custom_exceptions


def _empty_json_table_schema():
    '''Return an empty JSON table schema, as a JSON string.

    :rtype: string

    '''
    return json.dumps({'fields': []})


@toolkit.side_effect_free
def resource_schema_show(context, data_dict):
    '''Return the given resource's schema.

    :param resource_id: the ID of the resource whose schema should be returned
    :type resource_id: string

    :returns: the resource's schema
    :rtype: dict

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            ckanext.b2.logic.schema.resource_schema_show_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    assert not errors  # Nothing in resource_schema_show_schema ever adds
                       # errors to the errors dict.

    resource_id = data_dict.pop('resource_id')

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})
    schema = resource_dict.get('schema', _empty_json_table_schema())
    schema = json.loads(schema)
    return schema


@toolkit.side_effect_free
def resource_schema_field_show(context, data_dict):
    '''Return the given resource schema field.

    :param resource_id: the ID of the resource
    :type resource_id: string

    :param index: the index of the field to return
    :type index: int

    :returns: the field
    :rtype: dict

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            ckanext.b2.logic.schema.resource_schema_field_show_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': data_dict['resource_id']})
    field = schema['fields'][data_dict['index']]
    return field
