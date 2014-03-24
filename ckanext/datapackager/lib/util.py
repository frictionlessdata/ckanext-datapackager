'''Miscellaneous shared utility functions.

'''
import os.path

import ckanext.datapackager.exceptions as exceptions


def get_path_to_resource_file(resource_dict):
    '''Return the local filesystem path to an uploaded resource file.

    The given ``resource_dict`` should be for a resource whose file has been
    uploaded to the FileStore.

    :param resource_dict: dict of the resource whose file you want
    :type resource_dict: a resource dict, e.g. from action ``resource_show``

    :rtype: string
    :returns: the absolute path to the resource file on the local filesystem

    :raises ckanext.datapackager.exceptions.ResourceFileDoesNotExistException:
        If there is no uploaded file for the given resource (e.g. if the
        resource contains a link to a remote file instead)

    '''
    # We need to do a direct import here, there's no nicer way yet.
    import ckan.lib.uploader as uploader

    upload = uploader.ResourceUpload(resource_dict)
    path = upload.get_path(resource_dict['id'])
    path = os.path.abspath(path)

    if not os.path.isfile(path):
        raise exceptions.ResourceFileDoesNotExistException

    return path
