'''Action functions that we've had to copy-paste from CKAN into this extension.

The functions in this module should be copy-pasted from CKAN unmodified.

We have to duplicate these because CKAN doesn't have a "call my plugin's
function after an action function finishes" plugin interface yet, and the
action functions can't be wrapped because of clever code that prevents you from
calling them directly.

'''
import ckan.plugins.toolkit as toolkit

import ckan.lib.uploader as uploader
import ckan.logic as logic
_get_or_bust = logic.get_or_bust
_get_action = toolkit.get_action
_check_access = toolkit.check_access
ValidationError = logic.ValidationError


def resource_create(context, data_dict):
    '''Appends a new resource to a datasets list of resources.

    :param package_id: id of package that the resource needs should be added to.
    :type package_id: string
    :param url: url of resource
    :type url: string
    :param revision_id: (optional)
    :type revisiion_id: string
    :param description: (optional)
    :type description: string
    :param format: (optional)
    :type format: string
    :param hash: (optional)
    :type hash: string
    :param name: (optional)
    :type name: string
    :param resource_type: (optional)
    :type resource_type: string
    :param mimetype: (optional)
    :type mimetype: string
    :param mimetype_inner: (optional)
    :type mimetype_inner: string
    :param webstore_url: (optional)
    :type webstore_url: string
    :param cache_url: (optional)
    :type cache_url: string
    :param size: (optional)
    :type size: int
    :param created: (optional)
    :type created: iso date string
    :param last_modified: (optional)
    :type last_modified: iso date string
    :param cache_last_updated: (optional)
    :type cache_last_updated: iso date string
    :param webstore_last_updated: (optional)
    :type webstore_last_updated: iso date string
    :param upload: (optional)
    :type upload: FieldStorage (optional) needs multipart/form-data

    :returns: the newly created resource
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']

    package_id = _get_or_bust(data_dict, 'package_id')
    data_dict.pop('package_id')

    pkg_dict = _get_action('package_show')(context, {'id': package_id})

    _check_access('resource_create', context, data_dict)

    if not 'resources' in pkg_dict:
        pkg_dict['resources'] = []

    upload = uploader.ResourceUpload(data_dict)

    pkg_dict['resources'].append(data_dict)

    try:
        context['defer_commit'] = True
        context['use_cache'] = False
        _get_action('package_update')(context, pkg_dict)
        context.pop('defer_commit')
    except ValidationError, e:
        errors = e.error_dict['resources'][-1]
        raise ValidationError(errors)

    ## Get out resource_id resource from model as it will not appear in
    ## package_show until after commit
    upload.upload(context['package'].resources[-1].id,
                  uploader.get_max_resource_size())
    model.repo.commit()

    ##  Run package show again to get out actual last_resource
    pkg_dict = _get_action('package_show')(context, {'id': package_id})
    resource = pkg_dict['resources'][-1]

    return resource
