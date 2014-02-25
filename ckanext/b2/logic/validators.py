'''Validator functions used by schema.py.

'''
import ckan.plugins.toolkit as toolkit


def field_name_validator(key, data, errors, context):
    name = data[key]

    if not name:
        raise toolkit.Invalid(toolkit._("You can't have an empty field name"))

    # Make sure the resource doesn't already have a field with this name.
    resource_id = data[('resource_id',)]
    schema = toolkit.get_action('resource_schema_show')(
        context, {'resource_id': resource_id})
    for field in schema.get('fields', []):
        if field['name'] == name:
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
