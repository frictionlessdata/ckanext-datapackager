import ckan.model as model
import ckan.plugins.toolkit as toolkit


class DataPackageController(toolkit.BaseController):

    def new(self):
        data = {
            'owner_org': toolkit.request.params.get('group'),
        }

        return toolkit.render(
            'data_package/import_data_package.html',
            extra_vars={
                'data': data,
            }
        )

    def import_data_package(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user or toolkit.c.author,
        }
        dataset = toolkit.get_action('package_create_from_datapackage')(
            context,
            toolkit.request.params
        )
        toolkit.redirect_to(controller='package',
                            action='read',
                            id=dataset['id'])

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
