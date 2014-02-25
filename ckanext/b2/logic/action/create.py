import json

import ckan.plugins.toolkit as toolkit
import ckanext.b2.lib.util as util


def resource_schema_field_create(context, data_dict):
    '''Create a new field in a resource's schema.

    The schema is stored as a JSON string in the resource's ``schema`` field.

    If the resource doesn't have a schema yet one will be created.

    If the schema already contains a field with the given name, an error will
    be returned.

    Any other custom parameters beyond those described below can be given, and
    they will be stored in the field's entry in the schema.

    :param resource_id: the ID of the resource whose schema the field should be
                        added to
    :type resource: string

    :param name: the name of the field, this should match the field/column in
                 the data file if there is one
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

    :returns: the schema
    :rtype: dict

    '''
    # TODO: Validation.

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
    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    return schema
