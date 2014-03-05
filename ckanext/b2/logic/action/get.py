import json

import ckan.plugins.toolkit as toolkit
import ckan.lib.navl.dictization_functions as dictization_functions

import ckanext.b2.logic.schema
import ckanext.b2.exceptions as custom_exceptions
import ckanext.b2.lib.sdf as sdf


def _empty_json_table_schema():
    '''Return an empty JSON table schema, as a JSON string.

    :rtype: string

    '''
    return json.dumps({'fields': []})


@toolkit.side_effect_free
def resource_schema_show(context, data_dict):
    '''Return the given resource's schema.

    :param resource_id: the ID of the resource whose schema should be returned
    :type resource_id: string

    :returns: the resource's schema
    :rtype: dict

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            ckanext.b2.logic.schema.resource_schema_show_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    assert not errors  # Nothing in resource_schema_show_schema ever adds
                       # errors to the errors dict.

    resource_id = data_dict.pop('resource_id')

    resource_dict = toolkit.get_action('resource_show')(context,
        {'id': resource_id})
    schema = resource_dict.get('schema', _empty_json_table_schema())
    schema = json.loads(schema)
    return schema


@toolkit.side_effect_free
def resource_schema_field_show(context, data_dict):
    '''Return the given resource schema field.

    :param resource_id: the ID of the resource
    :type resource_id: string

    :param index: the index of the field to return
    :type index: int

    :returns: the field
    :rtype: dict

    '''
    try:
        data_dict, errors = dictization_functions.validate(data_dict,
            ckanext.b2.logic.schema.resource_schema_field_show_schema(),
            context)
    except custom_exceptions.InvalidResourceIDException, e:
        raise toolkit.ValidationError(e)
    if errors:
        raise toolkit.ValidationError(errors)

    schema = toolkit.get_action('resource_schema_show')(context,
        {'resource_id': data_dict['resource_id']})

    # Find the field with the given index.
    # Note - the field with index 3 is not necessarily the field at index 3
    # in the list of fields! There may not be fields with indices 0, 1 or 2,
    # and the fields may have been added out of order.
    field = None
    for field_ in schema['fields']:
        if field_['index'] == data_dict['index']:
            field = field_
            break
    assert field is not None, ("At this point we assume that a field with the "
                               "given index does exist, because it should "
                               "have already been validated.")
    return field


@toolkit.side_effect_free
def package_to_sdf(context, data_dict):
    '''Return the given CKAN package in dataprotocols.org Data Package format.

    This returns just the data package metadata in JSON format (what would be
    the contents of the datapackage.json file), it does not return the whole
    multi-file package including datapackage.json file and additional data
    files.

    If a zipstream.ZipFile object is provided with key "pkg_zipstream" in the
    context dict, then a datapackage.json file and data files for each of the
    package's resources (if the resource has a file uploaded to the FileStore)
    will be added into the zipstream.

    :param package_id: the ID of the package
    :type package_id: string

    :returns: the data package metadata
    :rtype: JSON

    '''
    try:
        package_id = data_dict['id']
    except KeyError:
        raise toolkit.ValidationError({'id': 'missing id'})

    pkg_dict = toolkit.get_action('package_show')(context,
                                                  {'name_or_id': package_id})
    return sdf.convert_to_sdf(pkg_dict,
        pkg_zipstream=context.get('pkg_zipstream'))