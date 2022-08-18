import json

import ckan.model as model
import ckan.plugins.toolkit as toolkit
from flask import make_response

def _authorize_or_abort(context):
    try:
        toolkit.check_access('package_create', context)
    except toolkit.NotAuthorized:
        toolkit.abort(401, toolkit._('Unauthorized to create a dataset'))

def new(data=None, errors=None, error_summary=None):
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
        'auth_user_obj': toolkit.c.userobj,
    }
    _authorize_or_abort(context)

    errors = errors or {}
    error_summary = error_summary or {}
    default_data = {
        'owner_org': toolkit.request.params.get('group'),
    }
    data = data or default_data

    return toolkit.render(
        'datapackage/import_datapackage.html',
        extra_vars={
            'pkg_dict': {},
            'data': data,
            'errors': errors,
            'error_summary': error_summary,
        }
    )

def import_datapackage():
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    _authorize_or_abort(context)

    try:
        if hasattr(toolkit.request, "form") and len(list(toolkit.request.form.keys())) > 0:
            params = toolkit.request.form.to_dict()
        else:
            params = toolkit.request.params

        if 'upload' in toolkit.request.files:
            params['upload'] = toolkit.request.files['upload']

        dataset = toolkit.get_action('package_create_from_datapackage')(
            context,
            params,
        )

        if toolkit.check_ckan_version(min_version="2.9"):
            return toolkit.redirect_to('dataset.read', id=dataset['name'])
        else:
            return toolkit.redirect_to('dataset_read', id=dataset['name'])

    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        return new(data=params,
                        errors=errors,
                        error_summary=error_summary)

def export_datapackage(package_id):
    '''Return the given dataset as a Data Package JSON file.

    '''
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }

    r = make_response() if toolkit.check_ckan_version(min_version="2.9") else toolkit.response
    r.content_disposition = 'attachment; filename=datapackage.json'.format(
        package_id)
    r.content_type = 'application/json'
    try:
        datapackage_dict = toolkit.get_action(
            'package_show_as_datapackage')(
            context,
            {'id': package_id}
        )
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, 'Dataset not found')

    if toolkit.check_ckan_version(min_version="2.9"):
        r.data = json.dumps(datapackage_dict, indent=2)
        return r
    else:
        return json.dumps(datapackage_dict, indent=2)


if not toolkit.check_ckan_version(u'2.9'):
    class DataPackageController(toolkit.BaseController):
        def new(self, data=None, errors=None, error_summary=None):
            return new(data, errors, error_summary)
        def import_datapackage(self):
            return import_datapackage()
        def export_datapackage(self, package_id):
            return export_datapackage(package_id)


