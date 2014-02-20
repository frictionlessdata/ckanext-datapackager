'''Custom action create functions provided by this extension.

'''
import os.path

import ckan.plugins.toolkit as toolkit

import ckanext.b2.lib.csv as lib_csv
import ckanext.b2.logic.action.duplicates as duplicates


def resource_create(context, data_dict):
    '''Wrap the core resource_create function and call our
    _after_resource_create() after it.

    This is what we like a CKAN plugin interface to do for us: call a plugin
    function after a given action function finishes.

    '''
    resource = duplicates.resource_create(context, data_dict)
    _after_resource_create(context, resource)


def _get_path_to_resource_file(resource_dict):
    '''Return the local filesystem path to an uploaded resource file.

    The given ``resource_dict`` should be for a resource whose file has been
    uploaded to the FileStore.

    :param resource_dict: dict of the resource whose file you want
    :type resource_dict: a resource dict, e.g. from action ``resource_show``

    :rtype: string
    :returns: the absolute path to the resource file on the local filesystem

    '''
    # We need to do a direct import here, there's no nicer way yet.
    import ckan.lib.uploader as uploader
    upload = uploader.ResourceUpload(resource_dict)
    path = upload.get_path(resource_dict['id'])
    return os.path.abspath(path)


def _infer_schema_for_resource(resource):
    '''Return a JSON Table Schema for the given resource.

    This will guess column headers and types from the resource's CSV file.

    Assumes a resource with a CSV file uploaded to the FileStore.

    '''
    path = _get_path_to_resource_file(resource)
    schema = lib_csv.infer_schema_from_csv_file(path)
    return schema

def _after_resource_create(context, resource):
    '''Add a schema to the given resource and save it.'''

    resource['schema'] = _infer_schema_for_resource(resource)
    toolkit.get_action('resource_update')(context, resource)
