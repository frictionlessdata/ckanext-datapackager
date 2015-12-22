import random
import cgi
import json
import tempfile
import ckan.plugins.toolkit as toolkit

import datapackage
import ckanext.datapackager.lib.tdf as tdf


def package_create_from_datapackage(context, data_dict):
    '''Create a new dataset (package) from a Data Package file.

    :param url: url of the datapackage (optional if `upload` is defined)
    :type url: string
    :param upload: the uploaded datapackage (optional if `url` is defined)
    :type upload: cgi.FieldStorage
    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'`` (optional, default:
        datapackage's name concatenated with a random string to avoid
        name collisions)
    :type name: string
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string
    '''
    url = data_dict.get('url')
    upload = data_dict.get('upload')
    if not url and upload is None:
        msg = {'url': ['you must define either a url or upload attribute']}
        raise toolkit.ValidationError(msg)

    dp = _load_and_validate_datapackage(url=url, upload=upload)

    pkg_dict = tdf.tdf_to_pkg_dict(dp)

    owner_org = data_dict.get('owner_org')
    if owner_org:
        pkg_dict['owner_org'] = owner_org

    private = data_dict.get('private')
    if private:
        pkg_dict['private'] = private

    name = data_dict.get('name')
    if name:
        pkg_dict['name'] = name

    resources = pkg_dict.get('resources', [])
    if resources:
        del pkg_dict['resources']

    res = _package_create_with_unique_name(context, pkg_dict, name)

    if resources:
        pkg_id = res['id']
        _create_resources(pkg_id, context, resources)
        res = toolkit.get_action('package_show')(context, {'id': pkg_id})

    return res


def _load_and_validate_datapackage(url=None, upload=None):
    try:
        if upload is not None:
            dp = datapackage.DataPackage(upload.file)
        else:
            dp = datapackage.DataPackage(url)

        dp.validate()
    except datapackage.exceptions.DataPackageException as e:
        msg = {'datapackage': [e.message]}
        raise toolkit.ValidationError(msg)

    if not dp.safe():
        msg = {'datapackage': ['the Data Package has unsafe attributes']}
        raise toolkit.ValidationError(msg)

    return dp


def _package_create_with_unique_name(context, pkg_dict, name=None):
    res = None
    if name:
        pkg_dict['name'] = name

    try:
        res = toolkit.get_action('package_create')(context, pkg_dict)
    except toolkit.ValidationError as e:
        if not name and \
           'That URL is already in use.' in e.error_dict.get('name', []):
            random_num = random.randint(0, 9999999999)
            name = '{name}-{rand}'.format(name=pkg_dict.get('name', 'dp'),
                                          rand=random_num)
            pkg_dict['name'] = name
            res = toolkit.get_action('package_create')(context, pkg_dict)
        else:
            raise e

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
        data = json.dumps(data, indent=2)

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
