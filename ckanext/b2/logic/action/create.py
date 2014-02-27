import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.b2.logic.schema
import ckanext.b2.exceptions as custom_exceptions


def resource_schema_field_create(context, data_dict):
    '''Create a new field in a resource's schema.

    The schema is stored as a JSON string in the resource's ``schema`` field.

    If the resource doesn't have a schema yet one will be created.

    If the schema already contains a field with the given index or name,
    a ValidationError will be raised. (If you want to update the attributes
    of an existing field, use
    :py:func:`~ckanext.b2.logic.action.update.resource_schema_field_update`.)

    Any other custom parameters beyond those described below can be given, and
    they will be stored in the field's entry in the schema. The values of these
    custom parameters will be converted to strings.

    :param resource_id: the ID of the resource whose schema the field should be
                        added to
    :type resource: string

    :param index: the index number of the column in the CSV file that this
        field corresponds to: 0 means the first column, 1 means the second
        column, and so on
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

    :returns: the field that was created
    :rtype: dict

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            ckanext.b2.logic.schema.resource_schema_field_create_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')

    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    schema['fields'].append(data_dict)
    schema = json.dumps(schema)

    # We need to pass the resource URL to resource_update or we get a
    # validation error, so we need to call resource_show() here to get it.
    url = toolkit.get_action('resource_show')(context,
                                              {'id': resource_id})['url']

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': url, 'schema': schema})

    # This is probably unnecessary as we already have the schema above.
    field = toolkit.get_action('resource_schema_field_show')(context,
        {'resource_id': resource_id, 'index': data_dict['index']})
    return field
