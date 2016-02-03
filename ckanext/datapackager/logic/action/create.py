import random
import cgi
import json
import tempfile
import ckan.plugins.toolkit as toolkit

import datapackage
import ckanext.datapackager.lib.converter as converter


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
    :param private: the visibility of the new dataset
    :type private: bool
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string
    '''
    url = data_dict.get('url')
    upload = data_dict.get('upload')
    if not url and not _upload_attribute_is_valid(upload):
        msg = {'url': ['you must define either a url or upload attribute']}
        raise toolkit.ValidationError(msg)

    dp = _load_and_validate_datapackage(url=url, upload=upload)

    dataset_dict = converter.datapackage_to_dataset(dp)

    owner_org = data_dict.get('owner_org')
    if owner_org:
        dataset_dict['owner_org'] = owner_org

    private = data_dict.get('private')
    if private:
        dataset_dict['private'] = toolkit.asbool(private)

    name = data_dict.get('name')
    if name:
        dataset_dict['name'] = name

    resources = dataset_dict.get('resources', [])
    if resources:
        del dataset_dict['resources']

    # Create as draft by default so if there's any issue on creating the
    # resources and we're unable to purge the dataset, at least it's not shown.
    dataset_dict['state'] = 'draft'
    res = _package_create_with_unique_name(context, dataset_dict, name)

    dataset_id = res['id']

    if resources:
        try:
            _create_resources(dataset_id, context, resources)
            res = toolkit.get_action('package_show')(context, {'id': dataset_id})
        except Exception as e:
            toolkit.get_action('package_delete')(context, {'id': dataset_id})
            raise e

    res['state'] = 'active'
    return toolkit.get_action('package_update')(context, res)


def _load_and_validate_datapackage(url=None, upload=None):
    try:
        if _upload_attribute_is_valid(upload):
            dp = datapackage.DataPackage(upload.file)
        else:
            dp = datapackage.DataPackage(url)

        dp.validate()
    except (datapackage.exceptions.DataPackageException,
            datapackage.exceptions.SchemaError,
            datapackage.exceptions.ValidationError) as e:
        msg = {'datapackage': [e.message]}
        raise toolkit.ValidationError(msg)

    if not dp.safe():
        msg = {'datapackage': ['the Data Package has unsafe attributes']}
        raise toolkit.ValidationError(msg)

    return dp


def _package_create_with_unique_name(context, dataset_dict, name=None):
    res = None
    if name:
        dataset_dict['name'] = name

    try:
        res = toolkit.get_action('package_create')(context, dataset_dict)
    except toolkit.ValidationError as e:
        if not name and \
           'That URL is already in use.' in e.error_dict.get('name', []):
            random_num = random.randint(0, 9999999999)
            name = '{name}-{rand}'.format(name=dataset_dict.get('name', 'dp'),
                                          rand=random_num)
            dataset_dict['name'] = name
            res = toolkit.get_action('package_create')(context, dataset_dict)
        else:
            raise

    return res


def _create_resources(dataset_id, context, resources):
    for resource in resources:
        resource['package_id'] = dataset_id
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
    if not isinstance(data, basestring):
        data = json.dumps(data, indent=2)

    with tempfile.NamedTemporaryFile(prefix=prefix) as f:
        f.write(data)
        f.seek(0)
        _create_and_upload_resource(context, resource, f)


def _create_and_upload_local_resource(context, resource):
    path = resource['path']
    del resource['path']
    try:
        with open(path, 'r') as f:
            _create_and_upload_resource(context, resource, f)
    except IOError:
        msg = {'datapackage': [(
            "Couldn't create some of the resources."
            " Please make sure that all resources' files are accessible."
        )]}
        raise toolkit.ValidationError(msg)


def _create_and_upload_resource(context, resource, the_file):
    resource['url'] = 'url'
    resource['url_type'] = 'upload'
    resource['upload'] = _UploadLocalFileStorage(the_file)
    toolkit.get_action('resource_create')(context, resource)


def _upload_attribute_is_valid(upload):
    return hasattr(upload, 'file') and hasattr(upload.file, 'read')


class _UploadLocalFileStorage(cgi.FieldStorage):
    def __init__(self, fp, *args, **kwargs):
        self.name = fp.name
        self.filename = fp.name
        self.file = fp
