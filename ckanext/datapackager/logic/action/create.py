import cgi
import json
import tempfile
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
        pkg_id = res['id']
        _create_resources(pkg_id, context, resources)
        res = toolkit.get_action('package_show')(context, {'id': pkg_id})

    return res


def _create_resources(pkg_id, context, resources):
    for resource in resources:
        resource['package_id'] = pkg_id
        if resource.get('data'):
            _create_and_upload_resource_with_inline_data(context, resource)
        elif resource.get('path'):
            _create_and_upload_local_resource(context, resource)
        else:
            toolkit.get_action('resource_create')(context, resource)


def _create_and_upload_resource_with_inline_data(context, resource):
    prefix = resource.get('name', 'tmp')
    data = resource['data']
    del resource['data']
    if not isinstance(data, str):
        data = json.dumps(data)

    with tempfile.NamedTemporaryFile(prefix=prefix) as f:
        f.write(data)
        f.seek(0)
        _create_and_upload_resource(context, resource, f)


def _create_and_upload_local_resource(context, resource):
    path = resource['path']
    del resource['path']
    with open(path, 'r') as f:
        _create_and_upload_resource(context, resource, f)


def _create_and_upload_resource(context, resource, the_file):
    resource['url'] = 'url'
    resource['url_type'] = 'upload'
    resource['upload'] = _UploadLocalFileStorage(the_file)
    toolkit.get_action('resource_create')(context, resource)


class _UploadLocalFileStorage(cgi.FieldStorage):
    def __init__(self, fp, *args, **kwargs):
        self.name = fp.name
        self.filename = fp.name
        self.file = fp
