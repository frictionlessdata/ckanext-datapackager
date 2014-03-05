'''Some library functions for dealing with Simple Data Format.

(Including converting CKAN's package and resource formats into SDF.)

'''
import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit


def _convert_to_sdf_resource(resource_dict, relative_path=False):
    '''Convert a CKAN resource dict into a Simple Data Format resource dict.

    '''
    if relative_path:
        name = resource_dict.get('name')
        if not name:
            name = toolkit._('Unnamed file')
        resource = {
            'path': name,
        }
    else:
        resource = {
            'url': resource_dict['url'],
        }
    try:
        schema_string = resource_dict.get('schema', '')
        resource['schema'] = h.json.loads(schema_string)
    except ValueError:
        pass
    return resource


def convert_to_sdf(pkg_dict, relative_paths=False):
    '''Convert the given CKAN package dict into a Simple Data Format dict.

    Convert the given package dict into a dict that, if dumped to a JSON
    string, can form the valid contents of the package descriptor file in a
    Simple Data Format data package.

    :param relative_paths: If True, each resource dict will contain the
        relative path to the resource in the data package ZIP file. If False,
        each resource dict will contain the URL to the online copy of the
        resource.
    :type relative_paths: boolean

    :returns: the data package dict
    :rtype: dict

    '''
    data_package = {
        'name': pkg_dict['name'],
        'resources': [_convert_to_sdf_resource(r, relative_paths)
                      for r in pkg_dict.get('resources', None)]
    }
    return data_package
