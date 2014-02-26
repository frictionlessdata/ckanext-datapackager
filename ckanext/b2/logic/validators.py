'''Validator functions used by schema.py.

'''
import ckan.plugins.toolkit as toolkit
import ckan.logic.validators as core_validators
import ckan.lib.navl.dictization_functions as df

import ckanext.b2.exceptions as custom_exceptions


def resource_id_validator(key, converted_data, errors, context):

    resource_id = converted_data.get(('resource_id',))
    if (not resource_id) or (resource_id is df.missing):
        raise custom_exceptions.InvalidResourceIDException(
                toolkit._("Missing resource_id argument"))

    resource_id = unicode(resource_id)

    try:
        core_validators.resource_id_exists(resource_id, context)
    except toolkit.Invalid:
        raise custom_exceptions.InvalidResourceIDException(
            toolkit._("Invalid resource_id"))


def create_field_index_validator(key, data, errors, context):

    index = data[key]

    try:
        index = int(index)
    except (ValueError, TypeError):
        raise toolkit.Invalid(toolkit._("index must be an int"))

    if index < 0:
        raise toolkit.Invalid(toolkit._("You can't have a negative index"))

    # Make sure the resource doesn't already have a field with this index.
    resource_id = data[('resource_id',)]
    schema = toolkit.get_action('resource_schema_show')(
        context, {'resource_id': resource_id})
    for field in schema.get('fields', []):
        if field['index'] == index:
            raise toolkit.Invalid(
                toolkit._("You can't have two fields with the same index"))

    # TODO: Here we could also prevent creating fields with indexes
    # corresponding to columns that don't actually exist in the resource's CSV
    # file.


def update_field_index_validator(key, data, errors, context):

    index = data[key]

    try:
        index = int(index)
    except (ValueError, TypeError):
        raise toolkit.Invalid(toolkit._("index must be an int"))

    if index < 0:
        raise toolkit.Invalid(toolkit._("You can't have a negative index"))

    # Make sure the resource has a field with this index.
    resource_id = data[('resource_id',)]
    try:
        schema = toolkit.get_action('resource_schema_show')(
            context, {'resource_id': resource_id})
    except toolkit.ObjectNotFound:
        raise toolkit.Invalid(toolkit._("Invalid resource_id"))
    matching_fields = []
    for field in schema.get('fields', []):
        if field['index'] == index:
            matching_fields.append(field)
    if len(matching_fields) == 0:
        raise toolkit.Invalid(toolkit._("There's no field with the given "
                                        "index"))
    if len(matching_fields) > 1:
        raise toolkit.Invalid(toolkit._("There's more than one field with the "
                                        "given index (this shouldn't happen, "
                                        "something has gone wrong)"))


def create_field_name_validator(key, data, errors, context):
    name = data[key]

    # Make sure the resource doesn't already have a field with this name.
    resource_id = data[('resource_id',)]
    schema = toolkit.get_action('resource_schema_show')(
        context, {'resource_id': resource_id})
    for field in schema.get('fields', []):
        if field['name'] == name:
            raise toolkit.Invalid(
                toolkit._("You can't have two fields with the same name"))


def update_field_name_validator(key, data, errors, context):
    name = data[key]
    index = data.get(('index',))

    resource_id = data[('resource_id',)]
    schema = toolkit.get_action('resource_schema_show')(
        context, {'resource_id': resource_id})
    for field in schema.get('fields', []):
        if field['index'] != index and field['name'] == name:
            raise toolkit.Invalid(
                toolkit._("You can't have two fields with the same name"))


def field_type_validator(value, context):
    valid_types = ('string', 'number', 'integer', 'date', 'time', 'datetime',
                   'boolean', 'binary', 'object', 'geopoint', 'geojson',
                   'array', 'any')
    if value in valid_types:
        return value
    else:
        raise toolkit.Invalid(
            toolkit._("Field type must be one of: {valid_types}").format(
                valid_types=valid_types))
