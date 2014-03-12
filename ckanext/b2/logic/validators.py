'''Validator functions used by schema.py.

'''
import os.path

import ckan.plugins.toolkit as toolkit
import ckan.logic.validators as core_validators
import ckan.lib.navl.dictization_functions as df

import ckanext.b2.exceptions as exceptions


def _is_name_unique(context, name, key, converted_data, package):

    resource_id = converted_data.get(('resources', key[1], 'id'))
    resources = package['resources']

    # Find any existing resources that have the same name as the new/updated
    # resource. We do a case-insensitive string comparison, we don't want our
    # ZIP files to contain files with the same name only in different case,
    # some filesystems are case-insensitive.
    matching_resources = [resource for resource in resources if
                          resource['name'].lower() == name.lower()]

    if matching_resources and (len(matching_resources) > 1 or
                               matching_resources[0]['id'] != resource_id):
        return False
    else:
        return True


def _generate_resource_name(context, key, converted_data, package):

    # Get the filename of the uploaded or linked-to file from the resource's
    # URL.
    name = converted_data.get(('resources', key[1], 'url'))

    if name.endswith('/'):
        name = name[:-1]
    name = name.split('/')[-1]

    if _is_name_unique(context, name, key, converted_data, package):
        return name
    else:
        name, extension = os.path.splitext(name)
        for i in range(2, 1000):
            new_name = "{0}_{1}{2}".format(name, i, extension)
            if _is_name_unique(context, new_name, key, converted_data, package):
                return new_name

        # If we get here then 2...999 were all taken.
        raise toolkit.Invalid(toolkit._("I got bored trying to come up with "
            "a unique name for this file, you'll have to supply one yourself"))


def resource_name_validator(key, converted_data, errors, context):
    '''Validator for the names of new or updated resources.

    If the user gave a name when creating or updating that resource, check that
    the name is unique among the package's resources. If it isn't unique,
    raise ValidationError.

    If the user did not give a name when creating or updating the resource
    (or they gave an empty name) generate a unique name for the resource.

    '''
    name = converted_data[key]
    package_id = converted_data[('id',)]
    package = toolkit.get_action('package_show')(context, {'id': package_id})

    if name:
        if not _is_name_unique(context, name, key, converted_data, package):
            raise toolkit.Invalid(toolkit._(
                "A data package can't contain two files with the same name"))
    else:
        name = _generate_resource_name(context, key, converted_data, package)
        converted_data[key] = name


def resource_id_validator(key, converted_data, errors, context):
    resource_id = converted_data.get(('resource_id',))
    if (not resource_id) or (resource_id is df.missing):
        raise exceptions.InvalidResourceIDException(toolkit._(
            "Missing resource_id argument"))

    resource_id = unicode(resource_id)

    try:
        core_validators.resource_id_exists(resource_id, context)
    except toolkit.Invalid:
        raise exceptions.InvalidResourceIDException(toolkit._(
            "Invalid resource_id"))


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

    data[key] = index


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
    # We're assuming that resource_id has already been validated and is valid,
    # so resource_schema_show() won't raise an exception here.
    schema = toolkit.get_action('resource_schema_show')(
        context, {'resource_id': resource_id})
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

    data[key] = index


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


def resource_format_validator(value, context):

    if not value:
        value = ''
    else:
        value = unicode(value)

    value = value.strip()

    if value:
        return value
    else:
        # Always set the resource format to CSV if none is given.
        # There's currently a CKAN pull request to implement guessing resource
        # formats from mime types, once that's merged we should adopt it
        # instead: <https://github.com/ckan/ckan/pull/1350>
        return 'csv'
