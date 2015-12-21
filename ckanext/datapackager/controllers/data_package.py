import ckan.model as model
import ckan.plugins.toolkit as toolkit


class DataPackageController(toolkit.BaseController):

    def new(self, data=None, errors=None, error_summary=None):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user or toolkit.c.author,
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
            'data_package/import_data_package.html',
            extra_vars={
                'data': data,
                'errors': errors,
                'error_summary': error_summary,
            }
        )

    def import_data_package(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user or toolkit.c.author,
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

    def download_tabular_data_format(self, package_id):
        '''Return the given package as a Tabular Data Format ZIP file.

        '''
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user or toolkit.c.author,
        }
        r = toolkit.response
        r.content_disposition = 'attachment; filename={0}.zip'.format(
            package_id)
        r.content_type = 'application/octet-stream'

        return toolkit.get_action('package_to_tabular_data_format_zip')(
            context,
            {'id': package_id}
        )

    def _authorize_or_abort(self, context):
        try:
            toolkit.check_access('package_create', context)
        except toolkit.NotAuthorized:
            toolkit.abort(401, toolkit._('Unauthorized to create a package'))
