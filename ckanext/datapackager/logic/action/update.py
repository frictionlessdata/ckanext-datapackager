import json
import uuid

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.datapackager.logic.schema as schema
import ckanext.datapackager.exceptions as exceptions
import ckanext.datapackager.lib.csv as csv
import ckanext.datapackager.lib.util as util


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
    except exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict.pop('resource_id')
    index = data_dict['index']

    resource_dict = toolkit.get_action('resource_show')(context,
                                                        {'id': resource_id})

    if data_dict.get('type') in ('date', 'time', 'datetime'):

        try:
            path = util.get_path_to_resource_file(resource_dict)
        except exceptions.ResourceFileDoesNotExistException:
            path = None

        if path:
            try:
                data_dict['temporal_extent'] = csv.temporal_extent(path,
                                                 column_num=data_dict['index'])
            except ValueError:
                pass
            except TypeError:
                pass

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


def resource_schema_fkey_update(context, data_dict):
    '''Update a foreign key to a resource's schema.

    :param resource_id: the ID of the resource
    :type resource_id: string

    :param referenced_resource_id: the resource_id of containing the field
        this foreign key is pointing to.
    :param referenced_resource_id: string

    :param referenced_field: the field referenced in the foreign csv file
    :type referenceed_field: string

    '''
    data_dict, errors = dictization_functions.validate(data_dict,
        schema.resource_schema_fkey_update_schema(), context)
    if errors:
        raise toolkit.ValidationError(errors)

    resource_id = data_dict['resource_id']

    schema_ = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': resource_id})

    current = schema_.get('foreignKeys', [])
    # we update by just removing the fkey with the id we are updating and
    # adding a new entry with same id
    fkeys = [i for i in current if i['fkey_uid'] != data_dict['fkey_uid']]
    fkeys.append({
        'fields': data_dict['field'],
        'fkey_uid': data_dict['fkey_uid'],
        'reference': {
            'resource': data_dict['referenced_resource'],
            'fields': data_dict['referenced_field'],
        }
    })

    schema_['foreignKeys'] = fkeys
    schema_ = json.dumps(schema_)

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})

    toolkit.get_action('resource_update')(context,
        {'id': resource_id, 'url': resource_dict['url'],
         'name': resource_dict['name'], 'schema': schema_})
