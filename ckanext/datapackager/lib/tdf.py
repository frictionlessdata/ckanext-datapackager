'''Some library functions for dealing with Tabular Data Format.

(Including converting CKAN's package and resource formats into SDF.)

'''
import os.path
import tempfile

import ckan.lib.helpers as h
import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.lib.util as util


def _convert_to_tdf_resource(resource_dict, pkg_zipstream=None):
    '''Convert a CKAN resource dict into a Tabular Data Format resource dict.

    :param pkg_zipstream: If given and if the resource has a file uploaded to
        the FileStore, then the file will be written to the zipstream and the
        returned dict will contain "path" instead of "url".
    :type pkg_zipstream: zipstream.ZipFile

    '''
    if pkg_zipstream and resource_dict.get('url_type') == 'upload':

        name = resource_dict.get('name')
        if not name:
            # FIXME: Need to generate unique names (unique within the
            # package) for unnamed files.
            name = toolkit._('Unnamed file')
        resource = {'path': name}

        # Add the resource file itself into the ZIP file.
        pkg_zipstream.write(util.get_path_to_resource_file(resource_dict),
                            arcname=resource['path'])

    else:
        resource = {'url': resource_dict['url']}

    try:
        schema_string = resource_dict.get('schema', '')
        resource['schema'] = h.json.loads(schema_string)
    except ValueError:
        pass
    return resource


def convert_to_tdf(pkg_dict, pkg_zipstream=None):
    '''Convert the given CKAN package dict into a Tabular Data Format dict.

    Convert the given package dict into a dict that, if dumped to a JSON
    string, can form the valid contents of the package descriptor file in a
    Tabular Data Format data package.

    :param pkg_zipstream: If given, a datapackage.json file and data files for
        each of the package's resources (if the resource has a file uploaded to
        the FileStore) will be written to the zipstream.
    :type pkg_zipstream: zipstream.ZipFile

    :returns: the data package dict
    :rtype: dict

    '''
    data_package = {
        'name': pkg_dict['name'],
        'resources': [_convert_to_tdf_resource(r, pkg_zipstream)
                      for r in pkg_dict.get('resources', None)]
    }

    if pkg_zipstream:
        # We are building a ZIP file for this package.

        tmp_dir = os.path.join(tempfile.gettempdir(), 'ckan-tdf')
        if not os.path.exists(tmp_dir):
            os.makedirs(os.path.join(tmp_dir))

        datapackage_path = os.path.join(tmp_dir, '{0}.json'.format(
            pkg_dict['id']))
        datapackage_file = open(datapackage_path, 'w+')
        datapackage_file.write(h.json.dumps(data_package, indent=2))
        datapackage_file.close()
        pkg_zipstream.write(datapackage_file.name, 'datapackage.json')

    return data_package
