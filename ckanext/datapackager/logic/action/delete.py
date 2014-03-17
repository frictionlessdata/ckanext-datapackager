import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.datapackager.logic.schema as schema
import ckanext.datapackager.exceptions as exceptions


def resource_schema_field_delete(context, data_dict):
    '''Delete a field from a resource's schema.

    :param resource_id: the ID of the resource whose schema the field should be
                        deleted from
    :type resource: string

    :param index: the index number of the field to delete
    :type index: int

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            schema.resource_schema_field_delete_schema(), context)
    except exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')
    index = data_dict['index']

    schema_ = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    new_fields = [field for field in schema_['fields']
                  if field['index'] != index]
    assert len(new_fields) == len(schema_['fields']) - 1
    schema_['fields'] = new_fields

    resource_dict = toolkit.get_action('resource_show')(context,
                                       {'id': resource_id})

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': json.dumps(schema_)})


def resource_schema_pkey_delete(context, data_dict):
    '''Delete a resource's schema's primary key.

    :param resource_id: the ID of the resource
    :type resource_id: string

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            schema.resource_schema_pkey_delete_schema(), context)
    except exceptions.InvalidResourceIDException:
        raise toolkit.ValidationError(toolkit._("Invalid resource_id"))
    assert not errors  # Nothing in resoource_schema_pkey_delete_schema ever
                       # adds anything to the errors dict.

    resource_id = data_dict.pop('resource_id')

    schema_ = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    if 'primaryKey' in schema_:
        del schema_['primaryKey']
    schema_ = json.dumps(schema_)

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': schema_})
