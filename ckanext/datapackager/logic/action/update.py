import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.datapackager.logic.schema as schema
import ckanext.datapackager.exceptions as custom_exceptions


def resource_schema_field_update(context, data_dict):
    '''Update a new field in a resource's schema.

    The schema is stored as a JSON string in the resource's ``schema`` field.

    Any other custom parameters beyond those described below can be given, and
    they will be stored in the field's entry in the schema. The values of these
    custom parameters will be converted to strings.

    :param resource_id: the ID of the resource whose schema should be updated
    :type resource: string

    :param index: the index number of the field to update, this is the number
                  of the column in the CSV file that the field corresponds to:
                  0 means the first column, 1 means the second column, and so
                  on
    :type index: int

    :param name: the name of the field, this should match the title of the
                 field/column in the data file if there is one
    :type name: string

    :param title: a nicer human readable label or title for the field
                  (optional)
    :type title: string

    :param description: a description of the field (optional)
    :type description: string

    :param type: the type of the field, one of ``"string"``, ``"number"``,
                 ``"integer"``, ``"date"``, ``"time"``, ``"datetime"``,
                 ``"boolean"``, ``"binary"``, ``"object"``, ``"geopoint"``,
                 ``"geojson"``, ``"array"`` or ``"any"``
                 (optional, default: ``"string"``)
    :type type: string

    :param format: a string specifying the format of the field,
                   e.g. ``"DD.MM.YYYY"`` for a field of type ``"date"``
                   (optional)
    :type format: string

    :returns: the updated field
    :rtype: dict

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            schema.resource_schema_field_update_schema(), context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')
    index = data_dict['index']

    schema_ = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})
    fields = schema_['fields']

    updated_fields = []
    found = False
    for field in fields:
        if field['index'] == index:
            assert found is False, ("There shouldn't be more than one field "
                                    "with the same index")
            updated_fields.append(data_dict)
            found = True
        else:
            updated_fields.append(field)
    assert found is True, ("There should be an existing field with the given "
                           "index")
    schema_['fields'] = updated_fields

    schema_ = json.dumps(schema_)

    resource_dict = toolkit.get_action('resource_show')(context,
                                                        {'id': resource_id})
    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': schema_})

    # This is probably unnecessary as we already have the field above.
    field = toolkit.get_action('resource_schema_field_show')(context,
        {'resource_id': resource_id, 'index': data_dict['index']})
    return field


def resource_schema_pkey_update(context, data_dict):
    '''Update resource's schema's primary key.

    :param resource_id: the ID of the resource
    :type resource_id: string

    :param pkey: the new value for the primary key, either the name of one of
        the fields or a list of field names from the resource's schema
    :type pkey: string or iterable of strings

    :returns: the updated primary key
    :rtype: string or list of strings

    '''
    data_dict, errors = dictization_functions.validate(data_dict,
        schema.resource_schema_pkey_update_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')

    schema_ = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    schema_['primaryKey'] = data_dict['pkey']
    schema_ = json.dumps(schema_)

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': schema_})

    # This is probably unnecessary as we already have the schema above.
    pkey = toolkit.get_action('resource_schema_pkey_show')(context,
        {'resource_id': resource_id})
    return pkey
