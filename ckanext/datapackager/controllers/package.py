import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit


class DataPackagerPackageController(toolkit.BaseController):

    def new_metadata(self, id, data=None, errors=None, error_summary=None):
        import ckan.model as model
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

    def view_metadata(self, package_id, resource_id):
        return toolkit.render('package/resource_schema.html')

    def view_metadata_field(self, package_id, resource_id, index):
        return toolkit.render('package/resource_schema_field.html')
