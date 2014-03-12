import os.path

import routes.mapper

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.common as common
import ckan.lib.navl.validators as navl_validators

import ckanext.datapackager.lib.helpers as custom_helpers
import ckanext.datapackager.lib.csv as lib_csv
import ckanext.datapackager.logic.action.create
import ckanext.datapackager.logic.action.update
import ckanext.datapackager.logic.action.get
import ckanext.datapackager.logic.action.delete
import ckanext.datapackager.logic.validators as custom_validators


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


class DataPackagerPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    '''The main plugin class for ckanext-datapackager.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IResourceUpload)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IDatasetForm)

    def update_config(self, config):
        '''Update CKAN's configuration.

        See IConfigurer.

        '''
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_resource('fanstatic', 'datapackager')

    def _default_routes(self, map_):
        '''Make all the CKAN default routes that we use.

        This re-makes some of the CKAN default routes, but only the ones that
        we want. Some of these have been modified from the defaults, e.g.
        replace "dataset" with "package" in URLs.

        '''
        GET = dict(method=['GET'])
        PUT = dict(method=['PUT'])
        POST = dict(method=['POST'])
        DELETE = dict(method=['DELETE'])
        GET_POST = dict(method=['GET', 'POST'])
        PUT_POST = dict(method=['PUT', 'POST'])

        map_.connect('home', '/', controller='home', action='index')

        with routes.mapper.SubMapper(map_, controller='user') as m:
            m.connect('/user/edit', action='edit')
            # Note: openid users have slashes in their ids, so need the
            # wildcard in the route.
            m.connect('user_edit', '/user/edit/{id:.*}', action='edit',
                    ckan_icon='cog')
            m.connect('user_delete', '/user/delete/{id}', action='delete')
            m.connect('/user/reset/{id:.*}', action='perform_reset')
            m.connect('register', '/user/register', action='register')
            m.connect('login', '/user/login', action='login')
            m.connect('/user/_logout', action='logout')
            m.connect('/user/logged_in', action='logged_in')
            m.connect('/user/logged_out', action='logged_out')
            m.connect('/user/logged_out_redirect', action='logged_out_page')
            m.connect('/user/reset', action='request_reset')
            m.connect('/user/me', action='me')
            m.connect('/user/set_lang/{lang}', action='set_lang')
            m.connect('user_datasets', '/user/{id:.*}', action='read',
                    ckan_icon='sitemap')

        with routes.mapper.SubMapper(map_, controller='package') as m:
            m.connect('add dataset', '/package/new', action='new')
            m.connect('/package/{action}',
                    requirements=dict(action='|'.join([
                        'list',
                        'autocomplete',
                    ])))

            m.connect('/package/{action}/{id}/{revision}', action='read_ajax',
                    requirements=dict(action='|'.join([
                        'read',
                        'edit',
                    ])))
            m.connect('/package/{action}/{id}',
                    requirements=dict(action='|'.join([
                        'read_ajax',
                        'history_ajax',
                        'delete',
                        'api_data',
                    ])))
            m.connect('dataset_edit', '/package/edit/{id}', action='edit',
                    ckan_icon='edit')
            m.connect('/package/{id}.{format}', action='read')
            m.connect('dataset_resources', '/package/files/{id}',
                    action='resources', ckan_icon='reorder')
            m.connect('dataset_read', '/package/{id}', action='read',
                    ckan_icon='sitemap')
            m.connect('/package/{id}/file/{resource_id}',
                    action='resource_read')
            m.connect('/package/{id}/file_delete/{resource_id}',
                    action='resource_delete')
            m.connect('resource_edit',
                      '/package/{id}/file_edit/{resource_id}',
                      action='resource_edit', ckan_icon='edit')
            m.connect('/package/{id}/file/{resource_id}/download',
                    action='resource_download')
            m.connect(
                '/package/{id}/file/{resource_id}/download/{filename}',
                action='resource_download')
            m.connect('/package/{id}/file/{resource_id}/embed',
                    action='resource_embedded_dataviewer')
            m.connect('/package/{id}/file/{resource_id}/viewer',
                    action='resource_embedded_dataviewer', width="960",
                    height="800")
            m.connect('/package/{id}/file/{resource_id}/preview',
                    action='resource_datapreview')

        map_.connect('/package/new_file/{id}', controller='package',
                     action='new_resource')

        register_list = [
            'package',
            'resource',
            'tag',
            'group',
            'related',
            'revision',
            'licenses',
            'rating',
            'user',
            'activity'
        ]
        register_list_str = '|'.join(register_list)

        with routes.mapper.SubMapper(map_, controller='api',
            path_prefix='/api{ver:/3|}', ver='/3') as m:
            m.connect('/action/{logic_function}', action='action',
                    conditions=GET_POST)

        # /api ver 1, 2, 3 or none
        with routes.mapper.SubMapper(map_, controller='api',
            path_prefix='/api{ver:/1|/2|/3|}', ver='/1') as m:
            m.connect('', action='get_api')
            m.connect('/search/{register}', action='search')

        # /api ver 1, 2 or none
        with routes.mapper.SubMapper(map_, controller='api',
            path_prefix='/api{ver:/1|/2|}', ver='/1') as m:
            m.connect('/tag_counts', action='tag_counts')
            m.connect('/rest', action='index')
            m.connect('/qos/throughput/', action='throughput', conditions=GET)

        # /api/rest ver 1, 2 or none
        with routes.mapper.SubMapper(map_, controller='api',
            path_prefix='/api{ver:/1|/2|}', ver='/1',
            requirements=dict(register=register_list_str)) as m:

            m.connect('/rest/{register}', action='list', conditions=GET)
            m.connect('/rest/{register}', action='create', conditions=POST)
            m.connect('/rest/{register}/{id}', action='show', conditions=GET)
            m.connect('/rest/{register}/{id}', action='update', conditions=PUT)
            m.connect('/rest/{register}/{id}', action='update',
                      conditions=POST)
            m.connect('/rest/{register}/{id}', action='delete',
                      conditions=DELETE)
            m.connect('/rest/{register}/{id}/:subregister', action='list',
                    conditions=GET)
            m.connect('/rest/{register}/{id}/:subregister', action='create',
                    conditions=POST)
            m.connect('/rest/{register}/{id}/:subregister/{id2}',
                      action='create', conditions=POST)
            m.connect('/rest/{register}/{id}/:subregister/{id2}',
                      action='show', conditions=GET)
            m.connect('/rest/{register}/{id}/:subregister/{id2}',
                      action='update', conditions=PUT)
            m.connect('/rest/{register}/{id}/:subregister/{id2}',
                      action='delete', conditions=DELETE)

        # /api/util ver 1, 2 or none
        with routes.mapper.SubMapper(map_, controller='api',
            path_prefix='/api{ver:/1|/2|}', ver='/1') as m:
            m.connect('/util/user/autocomplete', action='user_autocomplete')
            m.connect('/util/is_slug_valid', action='is_slug_valid',
                    conditions=GET)
            m.connect('/util/dataset/autocomplete',
                action='dataset_autocomplete', conditions=GET)
            m.connect('/util/tag/autocomplete', action='tag_autocomplete',
                    conditions=GET)
            m.connect('/util/resource/format_autocomplete',
                    action='format_autocomplete', conditions=GET)
            m.connect('/util/resource/format_icon',
                    action='format_icon', conditions=GET)
            m.connect('/util/group/autocomplete', action='group_autocomplete')
            m.connect('/util/markdown', action='markdown')
            m.connect('/util/dataset/munge_name', action='munge_package_name')
            m.connect('/util/dataset/munge_title_to_name',
                    action='munge_title_to_package_name')
            m.connect('/util/tag/munge', action='munge_tag')
            m.connect('/util/status', action='status')
            m.connect('/util/snippet/{snippet_path:.*}', action='snippet')
            m.connect('/i18n/{lang}', action='i18n_js_translations')

        with routes.mapper.SubMapper(map_,
            controller='ckan.controllers.storage:StorageAPIController') as m:
            m.connect('storage_api', '/api/storage', action='index')
            m.connect('storage_api_set_metadata',
                      '/api/storage/metadata/{label:.*}',
                      action='set_metadata', conditions=PUT_POST)
            m.connect('storage_api_get_metadata',
                      '/api/storage/metadata/{label:.*}',
                      action='get_metadata', conditions=GET)
            m.connect('storage_api_auth_request',
                    '/api/storage/auth/request/{label:.*}',
                    action='auth_request')
            m.connect('storage_api_auth_form',
                    '/api/storage/auth/form/{label:.*}',
                    action='auth_form')

        with routes.mapper.SubMapper(map_,
                controller='ckan.controllers.storage:StorageController') as m:
            m.connect('storage_upload', '/storage/upload',
                    action='upload')
            m.connect('storage_upload_handle', '/storage/upload_handle',
                    action='upload_handle')
            m.connect('storage_upload_success', '/storage/upload/success',
                    action='success')
            m.connect('storage_upload_success_empty', '/storage/upload/success_empty',
                    action='success_empty')
            m.connect('storage_file', '/storage/f/{label:.*}',
                    action='file')

        with routes.mapper.SubMapper(map_, controller='util') as m:
            m.connect('/i18n/strings_{lang}.js', action='i18n_js_strings')
            m.connect('/util/redirect', action='redirect')
            m.connect('/testing/primer', action='primer')
            m.connect('/testing/markup', action='markup')

        map_.connect('/*url', controller='template', action='view')

        return map_


    def after_map(self, map_):

        # We seem to have to connect at least some of the default routes in
        # both before_map() and after_map(), otherwise some of our changes of
        # "dataset" to "package" don't work some of the time.
        return self._default_routes(map_)

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
            controller='ckanext.datapackager.controllers.user:DataPackagerUserController',
            action='read')

        # After they logout just redirect people to the front page, not the
        # stupid 'You have been logged out' page that CKAN has by default.
        map_.redirect('/user/logged_out_redirect', '/')

        # This makes the second stage of the dataset creation process skip
        # straight to the dataset read page, instead of going to the third
        # stage, which we're not using.
        map_.connect('/dataset/new_metadata/{id}',
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='new_metadata')

        # Add in just the CKAN default routes that we're using.
        map_ = self._default_routes(map_)

        # This route matches any URL and sends them all to 404. All routes
        # except the ones defined above will be 404'd, including all CKAN's
        # default routes except the ones we add back in above.
        map_.connect(R'{url:.*}',
            controller='ckanext.datapackager.controllers.fourohfour:DataPackager404Controller',
            action='fourohfour')

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
                ckanext.datapackager.logic.action.create.resource_schema_field_create,
            'resource_schema_field_update':
                ckanext.datapackager.logic.action.update.resource_schema_field_update,
            'resource_schema_field_delete':
                ckanext.datapackager.logic.action.delete.resource_schema_field_delete,
            'resource_schema_show':
                ckanext.datapackager.logic.action.get.resource_schema_show,
            'resource_schema_field_show':
                ckanext.datapackager.logic.action.get.resource_schema_field_show,
        }

    def package_types(self):
        '''Return the list of package types that this plugin handles as an
        IDatasetForm plugin.

        '''
        # Even though we're not using this feature, we have to return something
        # iterable here or CKAN crashes.
        return []

    def is_fallback(self):
        # Make this plugin the default IDatasetForm plugin.
        return True

    def _modify_package_schema(self, schema):
        schema['resources']['name'] = [
            custom_validators.resource_name_validator]
        schema['resources']['format'] = [
            navl_validators.ignore_missing,
            custom_validators.resource_format_validator,
        ]
        return schema

    def create_package_schema(self):

        schema = super(DataPackagerPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):

        schema = super(DataPackagerPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema
