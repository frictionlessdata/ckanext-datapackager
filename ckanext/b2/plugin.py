import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers

import ckanext.b2.lib.helpers as custom_helpers
import ckanext.b2.actions as custom_actions


class B2UserController(toolkit.BaseController):
    '''A simple user controller class.

    Takes over some of the default user routes from the default user
    controller.

    '''
    def read(self, locale=None):
        '''Render the logged-in user's profile page.

        If no user is logged in, redirects to the login page.

        '''
        if not toolkit.c.user:
            helpers.redirect_to(locale=locale, controller='user',
                                action='login', id=None)
        user_ref = toolkit.c.userobj.get_reference_preferred_for_uri()
        helpers.redirect_to(locale=locale, controller='user', action='read',
                            id=user_ref)


class B2PackageController(toolkit.BaseController):

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
                      controller='ckanext.b2.plugin:B2UserController',
                      action='read')

        # After they logout just redirect people to the front page, not the
        # stupid 'You have been logged out' page that CKAN has by default.
        map_.redirect('/user/logged_out_redirect', '/')

        map_.connect('/dataset/new_metadata/{id}',
            controller='ckanext.b2.plugin:B2PackageController',
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
