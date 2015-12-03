import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.lib.tdf as tdf


@toolkit.side_effect_free
def package_to_tabular_data_format(context, data_dict):
    '''Return the given CKAN package in Tabular Data Format.

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
    return tdf.convert_to_tdf(pkg_dict, pkg_zipstream=context.get('pkg_zipstream'))
