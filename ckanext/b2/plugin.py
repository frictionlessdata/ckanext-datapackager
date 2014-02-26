import os.path

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.common as common

import ckanext.b2.lib.helpers as custom_helpers
import ckanext.b2.lib.csv as lib_csv
import ckanext.b2.logic.action.create
import ckanext.b2.logic.action.update
import ckanext.b2.logic.action.get
import ckanext.b2.logic.action.delete


def _get_path_to_resource_file(resource_dict):
    '''Return the local filesystem path to an uploaded resource file.

    The given ``resource_dict`` should be for a resource whose file has been
    uploaded to the FileStore.

    :param resource_dict: dict of the resource whose file you want
    :type resource_dict: a resource dict, e.g. from action ``resource_show``

    :rtype: string
    :returns: the absolute path to the resource file on the local filesystem

    '''
    # We need to do a direct import here, there's no nicer way yet.
    import ckan.lib.uploader as uploader
    upload = uploader.ResourceUpload(resource_dict)
    path = upload.get_path(resource_dict['id'])
    return os.path.abspath(path)


def _infer_schema_for_resource(resource):
    '''Return a JSON Table Schema for the given resource.

    This will guess column headers and types from the resource's CSV file.

    Assumes a resource with a CSV file uploaded to the FileStore.

    '''
    path = _get_path_to_resource_file(resource)
    schema = lib_csv.infer_schema_from_csv_file(path)
    return schema


class B2Plugin(plugins.SingletonPlugin):
    '''The main plugin class for ckanext-b2.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IResourceUpload)
    plugins.implements(plugins.IActions)

    def update_config(self, config):
        '''Update CKAN's configuration.

        See IConfigurer.

        '''
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('fanstatic', 'b2')

    def before_map(self, map_):
        '''Customize CKAN's route map and return it.

        CKAN calls this method before the default routes map is generated, so
        any routes set in this method will override any conflicting default
        routes.

        See IRoutes and http://routes.readthedocs.org

        '''
        # After you login or register CKAN redirects you to your user dashboard
        # page. We're not using CKAN's user dashboard (we're just using user
        # profile pages as dashboards instead) so redirect /dashboard to
        # /user/{user_name}.
        # (Note the URL requires the user name which is not available in this
        # method, that's why we seem to need our own controller and action
        # method to handle the redirect.)
        map_.connect('/dashboard',
            controller='ckanext.b2.controllers.user:B2UserController',
            action='read')

        # After they logout just redirect people to the front page, not the
        # stupid 'You have been logged out' page that CKAN has by default.
        map_.redirect('/user/logged_out_redirect', '/')

        map_.connect('/dataset/new_metadata/{id}',
            controller='ckanext.b2.controllers.package:B2PackageController',
            action='new_metadata')

        return map_

    def get_helpers(self):
        '''Return this plugin's custom template helper functions.

        See ITemplateHelpers.

        '''
        return {'resource_display_name': custom_helpers.resource_display_name}

    def after_upload(self, context, resource):
        resource['schema'] = common.json.dumps(
            _infer_schema_for_resource(resource))
        toolkit.get_action('resource_update')(context, resource)

    def get_actions(self):
        return {
            'resource_schema_field_create':
                ckanext.b2.logic.action.create.resource_schema_field_create,
            'resource_schema_field_update':
                ckanext.b2.logic.action.update.resource_schema_field_update,
            'resource_schema_field_delete':
                ckanext.b2.logic.action.delete.resource_schema_field_delete,
            'resource_schema_show':
                ckanext.b2.logic.action.get.resource_schema_show,
            'resource_schema_field_show':
                ckanext.b2.logic.action.get.resource_schema_field_show,
        }
