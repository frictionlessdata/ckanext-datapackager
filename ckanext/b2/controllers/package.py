import tempfile
import os

import zipstream

import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.b2.lib.util as util


class B2PackageController(toolkit.BaseController):

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

        context['relative_paths'] = True
        datapackage_dict = toolkit.get_action('package_to_sdf')(context,
            {'id': package_id})

        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)

        pkg_dict = toolkit.get_action('package_show')(context,
                                                    {'name_or_id': package_id})
        for resource in pkg_dict['resources']:

            path = util.get_path_to_resource_file(resource)

            name = resource.get('name')
            if not name:
                name = toolkit._('Unnamed file')

            z.write(path, arcname=name)

        tmp_dir = os.path.join(tempfile.gettempdir(), 'ckan-sdf')
        if not os.path.exists(tmp_dir):
            os.makedirs(os.path.join(tmp_dir))

        datapackage_path = os.path.join(tmp_dir, '{0}.json'.format(package_id))
        datapackage_file = open(datapackage_path, 'w+')
        datapackage_file.write(helpers.json.dumps(datapackage_dict, indent=2))
        datapackage_file.close()
        z.write(datapackage_file.name, 'datapackage.json')

        return z
