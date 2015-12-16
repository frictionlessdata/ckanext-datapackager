import ckan.model as model
import ckan.plugins.toolkit as toolkit


class DataPackagerPackageController(toolkit.BaseController):

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
