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
    PARSERS = [
        _parse_title_and_version,
        _parse_license,
        _parse_author_and_source,
        _parse_maintainer,
        _parse_tags,
        _parse_extras,
    ]
    data_package = {
        'name': pkg_dict['name']
    }

    for parser in PARSERS:
        data_package.update(parser(pkg_dict))

    resources = pkg_dict.get('resources')
    if resources:
        data_package['resources'] = [_convert_to_tdf_resource(r, pkg_zipstream)
                                     for r in resources]

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


def _parse_title_and_version(pkg_dict):
    ATTRIBUTES = ['title', 'version']
    result = {}
    for attribute in ATTRIBUTES:
        if pkg_dict.get(attribute):
            result[attribute] = pkg_dict[attribute]
    return result


def _parse_license(pkg_dict):
    result = {}
    license = {}

    if pkg_dict.get('license_id'):
        license['type'] = pkg_dict['license_id']
    if pkg_dict.get('license_title'):
        license['title'] = pkg_dict['license_title']
    if pkg_dict.get('license_url'):
        license['url'] = pkg_dict['license_url']

    if license:
        result['license'] = license

    return result


def _parse_author_and_source(pkg_dict):
    result = {}
    source = {}

    if pkg_dict.get('author'):
        source['name'] = pkg_dict['author']
    if pkg_dict.get('author_email'):
        source['email'] = pkg_dict['author_email']
    if pkg_dict.get('source'):
        source['web'] = pkg_dict['source']

    if source:
        result['sources'] = [source]

    return result


def _parse_maintainer(pkg_dict):
    result = {}
    author = {}

    if pkg_dict.get('maintainer'):
        author['name'] = pkg_dict['maintainer']
    if pkg_dict.get('maintainer_email'):
        author['email'] = pkg_dict['maintainer_email']

    if author:
        result['author'] = author

    return result


def _parse_tags(pkg_dict):
    result = {}

    keywords = [tag['name'] for tag in pkg_dict.get('tags', [])]

    if keywords:
        result['keywords'] = keywords

    return result


def _parse_extras(pkg_dict):
    result = {}

    extras = [(extra['key'], extra['value']) for extra
              in pkg_dict.get('extras', [])]

    if extras:
        result.update(dict(extras))

    return result
