import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers


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


class B2Plugin(plugins.SingletonPlugin):
    '''The main plugin class for ckanext-b2.

    '''
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes)

    def update_config(self, config):
        '''Update CKAN's configuration.

        See IConfigurer.

        '''
        toolkit.add_template_directory(config, 'templates')

    def before_map(self, map_):
        '''Customize CKAN's route map and return it.

        CKAN calls this method before the default routes map is generated, so
        any routes set in this method will override any conflicting default
        routes.

        See IRotues and http://routes.readthedocs.org

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

        return map_

    def after_map(self, map_):
        '''Customize CKAN's route map and return it.

        CKAN calls this method after the default routes map is generated, so
        any routes set in this method will be overridden by any conflicting
        default routes. This method can be used to set fallback route handlers.

        See IRotues and http://routes.readthedocs.org

        '''
        return map_
