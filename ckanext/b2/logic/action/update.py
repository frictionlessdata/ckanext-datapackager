import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.b2.logic.schema
import ckanext.b2.exceptions as custom_exceptions


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
            ckanext.b2.logic.schema.resource_schema_field_update_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')
    index = data_dict['index']

    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})
    fields = schema['fields']

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
    schema['fields'] = updated_fields

    schema = json.dumps(schema)
    # We need to pass the resource URL to resource_update or we get a
    # validation error, so we need to call resource_show() here to get it.
    url = toolkit.get_action('resource_show')(context,
                                              {'id': resource_id})['url']
    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': url, 'schema': schema})

    # This is probably unnecessary as we already have the schema above.
    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})
    field = schema['fields'][data_dict['index']]
    return field
