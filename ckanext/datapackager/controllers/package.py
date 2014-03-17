import zipstream

import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit


class DataPackagerPackageController(toolkit.BaseController):

    def new_metadata(self, id, data=None, errors=None, error_summary=None):
        import ckan.lib.base as base

        # Change the package state from draft to active and save it.
        context = {'model': model, 'session': model.Session,
                   'user': toolkit.c.user or toolkit.c.author,
                   'auth_user_obj': toolkit.c.userobj}
        data_dict = toolkit.get_action('package_show')(context, {'id': id})
        data_dict['id'] = id
        data_dict['state'] = 'active'
        toolkit.get_action('package_update')(context, data_dict)

        base.redirect(helpers.url_for(controller='package', action='read',
                                      id=id))

    def download_sdf(self, package_id):
        '''Return the given package as a Simple Data Format ZIP file.

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

        # Make a zipstream and put it in the context. This means the
        # package_to_sdf action will add files into the zipstream for us.
        pkg_zipstream = zipstream.ZipFile(mode='w',
                                          compression=zipstream.ZIP_DEFLATED)
        context['pkg_zipstream'] = pkg_zipstream

        toolkit.get_action('package_to_sdf')(context, {'id': package_id})

        return pkg_zipstream
