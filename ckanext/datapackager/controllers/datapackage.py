import json

import ckan.model as model
import ckan.plugins.toolkit as toolkit


class DataPackageController(toolkit.BaseController):

    def new(self, data=None, errors=None, error_summary=None):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
            'auth_user_obj': toolkit.c.userobj,
        }
        self._authorize_or_abort(context)

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
            }
        )

    def import_datapackage(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
        }
        self._authorize_or_abort(context)

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
            return self.new(data=params,
                            errors=errors,
                            error_summary=error_summary)

    def export_datapackage(self, package_id):
        '''Return the given dataset as a Data Package JSON file.

        '''
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
        }
        r = toolkit.response
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
            toolkit.abort(404, 'Dataset not found')

        return json.dumps(datapackage_dict, indent=2)

    def _authorize_or_abort(self, context):
        try:
            toolkit.check_access('package_create', context)
        except toolkit.NotAuthorized:
            toolkit.abort(401, toolkit._('Unauthorized to create a dataset'))
