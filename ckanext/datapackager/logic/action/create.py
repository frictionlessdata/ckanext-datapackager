import ckan.plugins.toolkit as toolkit

import datapackage
import ckanext.datapackager.lib.tdf as tdf


def package_create_from_datapackage(context, data_dict):
    '''Create a new dataset (package) from a Data Package file.

    :param url: url of the datapackage
    :type url: string
    '''
    try:
        url = data_dict['url']
    except KeyError:
        raise toolkit.ValidationError({'url': 'missing url'})

    dp = datapackage.DataPackage(url)
    pkg_dict = tdf.tdf_to_pkg_dict(dp)

    return toolkit.get_action('package_create')(context, pkg_dict)
