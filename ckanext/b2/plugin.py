import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.b2.lib.helpers as custom_helpers
import ckanext.b2.actions as custom_actions


class B2Plugin(plugins.SingletonPlugin):
    '''The main plugin class for ckanext-b2.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
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

    def get_actions(self):
        '''Return the action functions that this plugin provides.

        See IActions.

        '''
        return {'resource_create': custom_actions.resource_create}
