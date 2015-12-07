'''Some library functions for dealing with Tabular Data Format.

(Including converting CKAN's package and resource formats into SDF.)

'''
import slugify

import datapackage
import ckan.lib.helpers as h

import ckanext.datapackager.lib.util as util


def _convert_to_tdf_resource(resource_dict):
    '''Convert a CKAN resource dict into a Tabular Data Format resource dict.

    '''
    resource = {}

    if resource_dict.get('url_type') == 'upload':
        resource['path'] = util.get_path_to_resource_file(resource_dict)
    else:
        if resource_dict.get('url'):
            resource['url'] = resource_dict['url']

    if resource_dict.get('description'):
        resource['description'] = resource_dict['description']

    if resource_dict.get('format'):
        resource['format'] = resource_dict['format']

    if resource_dict.get('hash'):
        resource['hash'] = resource_dict['hash']

    if resource_dict.get('name'):
        resource['name'] = slugify.slugify(resource_dict['name'])

    try:
        schema_string = resource_dict.get('schema', '')
        resource['schema'] = h.json.loads(schema_string)
    except ValueError:
        pass
    return resource


def convert_to_tdf_zip(pkg_dict, file_or_path):
    '''Saves the given CKAN package dict into a Tabular Data Format package.

    Convert the given package dict into a Data Package and saves it into the
    file or path received as parameter.

    :param file_or_path: Where to write the Data Package zip file into. It can
        either be a path or a file-like object.
    :type file_or_path: str or file-like object
    '''
    tdf_dict = convert_to_tdf(pkg_dict)
    # FIXME: This should use the "tabular" schema, but there're some issues
    # with it.
    data_package = datapackage.DataPackage(tdf_dict)
    data_package.save(file_or_path)


def convert_to_tdf(pkg_dict):
    '''Convert the given CKAN package dict into a Tabular Data Format dict.

    Convert the given package dict into a dict that, if dumped to a JSON
    string, can form the valid contents of the package descriptor file in a
    Tabular Data Format data package.

    :returns: the data package dict
    :rtype: dict

    '''
    PARSERS = [
        _parse_title_and_version,
        _parse_notes,
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
        data_package['resources'] = [_convert_to_tdf_resource(r)
                                     for r in resources]

    return data_package


def _parse_title_and_version(pkg_dict):
    ATTRIBUTES = ['title', 'version']
    result = {}
    for attribute in ATTRIBUTES:
        if pkg_dict.get(attribute):
            result[attribute] = pkg_dict[attribute]
    return result


def _parse_notes(pkg_dict):
    result = {}

    if pkg_dict.get('notes'):
        result['description'] = pkg_dict['notes']

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
        result['extras'] = dict(extras)

    return result
