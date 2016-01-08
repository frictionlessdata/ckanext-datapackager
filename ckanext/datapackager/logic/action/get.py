import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.lib.converter as converter


@toolkit.side_effect_free
def package_show_as_datapackage(context, data_dict):
    '''Return the given CKAN dataset into a Data Package.

    This returns just the data package metadata in JSON format (what would be
    the contents of the datapackage.json file), it does not return the whole
    multi-file package including datapackage.json file and additional data
    files.

    :param id: the ID of the dataset
    :type id: string

    :returns: the datapackage metadata
    :rtype: JSON

    '''
    try:
        dataset_id = data_dict['id']
    except KeyError:
        raise toolkit.ValidationError({'id': 'missing id'})

    dataset_dict = toolkit.get_action('package_show')(context,
                                                      {'id': dataset_id})

    return converter.dataset_to_datapackage(dataset_dict)
