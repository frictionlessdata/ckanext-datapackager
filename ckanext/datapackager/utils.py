import ckan.model as model
import ckan.plugins.toolkit as toolkit


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
            'data': data,
            'errors': errors,
            'error_summary': error_summary,
            'pkg_dict': {'type': ''}
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
        params = toolkit.request.params
        dataset = toolkit.get_action('package_create_from_datapackage')(
            context,
            params,
        )
        toolkit.redirect_to(controller='package',
                            action='read',
                            id=dataset['name'])
    except toolkit.ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        return new(
            data=params,
            errors=errors,
            error_summary=error_summary)
