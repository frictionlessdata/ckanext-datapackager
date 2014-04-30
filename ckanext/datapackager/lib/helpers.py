'''Some custom template helper functions.

'''
import unicodecsv
import itertools

import ckan.lib.helpers as helpers
import ckan.model as model
import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.lib.util as util
import ckanext.datapackager.exceptions as exceptions


def resource_display_name(*args, **kwargs):
    '''Return a display name for the given resource.

    This overrides CKAN's default resource_display_name template helper
    function and replaces 'Unnamed resource' with 'Unnamed file'.

    '''
    display_name = helpers.resource_display_name(*args, **kwargs)
    if display_name == 'Unnamed resource':
        display_name = 'Unnamed file'
    return display_name


def get_resource_schema(resource_id):
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    schema_show = toolkit.get_action('resource_schema_show')
    try:
        return schema_show(context, {'resource_id': resource_id})
    except toolkit.ValidationError:
        return {}


def resource_schema_field_show(resource_id, index):
    '''A wrapper for the resource_schema_field_show action function.

    So templates can call the action function.

    '''
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    schema_field_show = toolkit.get_action('resource_schema_field_show')
    data_dict = {'resource_id': resource_id, 'index': index}
    try:
        return schema_field_show(context, data_dict)
    except toolkit.ValidationError:
        return {}

def get_resource(resource_id):

    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    resource_show = toolkit.get_action('resource_show')
    return resource_show(context,{'id': resource_id})


def _csv_data_from_file(csv_file, preview_limit=10):

    try:
        dialect = unicodecsv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        csv_reader = unicodecsv.reader(csv_file, dialect)
        csv_values = itertools.islice(csv_reader, preview_limit)
        csv_values = zip(*csv_values)
        return {'success': True, 'data': csv_values}
    except unicodecsv.Error as exc:
        return {'success': False, 'error': exc.message}
    except UnicodeDecodeError as exc:
        return {'success': False, 'error': exc}


def csv_data(resource):
    '''Return the CSV data for the given resource.

    '''
    try:
        path = util.get_path_to_resource_file(resource)
    except exceptions.ResourceFileDoesNotExistException:
        return {'success': False,
                'error': toolkit._("There's no uploaded file for this "
                                   "resource")}
    return _csv_data_from_file(open(path))


def group_by_name(schema):
    '''Return a schema dict regrouped by name

    regroups a schema into a dict where the key is the name of the schema
    field and value is the index of the schema field
    '''
    try:
        by_name = dict((i['name'], i['index']) for i in schema['fields'])
        return by_name
    except KeyError:
        return None


def get_fkey_with_reference(fkey):
    '''iterates over foreign keys and their reference fields together'''
    try:
        return zip(fkey['fields'], fkey['reference']['fields'])
    except KeyError:
        return []
