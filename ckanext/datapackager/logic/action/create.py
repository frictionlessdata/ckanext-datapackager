import cgi
import ckan.plugins.toolkit as toolkit

import datapackage
import ckanext.datapackager.lib.tdf as tdf


def package_create_from_datapackage(context, data_dict):
    '''Create a new dataset (package) from a Data Package file.

    :param url: url of the datapackage
    :type url: string
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string
    '''
    try:
        url = data_dict['url']
    except KeyError:
        raise toolkit.ValidationError({'url': 'missing url'})

    dp = datapackage.DataPackage(url)
    pkg_dict = tdf.tdf_to_pkg_dict(dp)

    owner_org = data_dict.get('owner_org')
    if owner_org:
        pkg_dict['owner_org'] = owner_org

    resources = pkg_dict.get('resources', [])
    if resources:
        del pkg_dict['resources']
    res = toolkit.get_action('package_create')(context, pkg_dict)

    if resources:
        for resource in resources:
            resource['package_id'] = res['id']
            path = resource.get('path')
            if path:
                resource['url'] = path
                resource['url_type'] = 'upload'
                # FIXME: Close this file
                resource['upload'] = _UploadLocalFileStorage(open(path, 'r'))
                del resource['path']
            toolkit.get_action('resource_create')(context, resource)

        res = toolkit.get_action('package_show')(context, {'id': res['id']})

    return res


class _UploadLocalFileStorage(cgi.FieldStorage):
    def __init__(self, fp, *args, **kwargs):
        self.name = fp.name
        self.filename = fp.name
        self.file = fp
