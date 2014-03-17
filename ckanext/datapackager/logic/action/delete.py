import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.datapackager.logic.schema
import ckanext.datapackager.logic.validators
import ckanext.datapackager.exceptions as custom_exceptions


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
            ckanext.datapackager.logic.schema.resource_schema_field_delete_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')
    index = data_dict['index']

    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    new_fields = [field for field in schema['fields']
                  if field['index'] != index]
    assert len(new_fields) == len(schema['fields']) - 1
    schema['fields'] = new_fields

    resource_dict = toolkit.get_action('resource_show')(context,
                                       {'id': resource_id})

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': json.dumps(schema)})
