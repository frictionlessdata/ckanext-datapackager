'''Custom user controller(s).

'''
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helpers


class DataPackagerUserController(toolkit.BaseController):
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
