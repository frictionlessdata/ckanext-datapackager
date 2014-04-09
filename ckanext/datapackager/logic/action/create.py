import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.datapackager.logic.schema as schema
import ckanext.datapackager.exceptions as exceptions
import ckanext.datapackager.lib.csv_utils as csv_utils
import ckanext.datapackager.lib.util as util


def resource_schema_field_create(context, data_dict):
    '''Create a new field in a resource's schema.

    The schema is stored as a JSON string in the resource's ``schema`` field.

    If the resource doesn't have a schema yet one will be created.

    If the schema already contains a field with the given index or name,
    a ValidationError will be raised. (If you want to update the attributes
    of an existing field, use
    :py:func:`~ckanext.datapackager.logic.action.update.resource_schema_field_update`.)

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
            schema.resource_schema_field_create_schema(), context)
    except exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})

    if data_dict.get('type') in ('date', 'time', 'datetime'):

        try:
            path = util.get_path_to_resource_file(resource_dict)
        except exceptions.ResourceFileDoesNotExistException:
            path = None

        if path:
            try:
                data_dict['temporal_extent'] = csv_utils.temporal_extent(path,
                                                 column_num=data_dict['index'])
            except ValueError:
                pass
            except TypeError:
                pass

    schema_ = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})
    schema_['fields'].append(data_dict)
    schema_ = json.dumps(schema_)

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': schema_})

    # This is probably unnecessary as we already have the schema above.
    field = toolkit.get_action('resource_schema_field_show')(context,
        {'resource_id': resource_id, 'index': data_dict['index']})

    return field


def resource_schema_pkey_create(context, data_dict):
    '''Add a primary key to a resource's schema.

    :param resource_id: the ID of the resource
    :type resource_id: string

    :param pkey: the primary key, either the name of one of the fields or a
        list of field names from the resource's schema
    :type pkey: string or iterable of strings

    :returns: the primary key that was created
    :rtype: string or list of strings

    '''
    # Fail if the resource already has a primary key.
    resource_id = toolkit.get_or_bust(data_dict, 'resource_id')
    try:
        pkey = toolkit.get_action('resource_schema_pkey_show')(context,
            {'resource_id': resource_id})
    except exceptions.InvalidResourceIDException:
        raise toolkit.ValidationError(toolkit._("Invalid resource_id"))
    if pkey is not None:
        raise toolkit.ValidationError(toolkit._("The resource already has a "
                                                "primary key"))

    # Otherwise create is the same as update.
    return toolkit.get_action('resource_schema_pkey_update')(context,
                                                             data_dict)
