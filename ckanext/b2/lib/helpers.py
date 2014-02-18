'''Some custom template helper functions.

'''
import ckan.lib.helpers as helpers


def resource_display_name(*args, **kwargs):
    '''Return a display name for the given resource.

    This overrides CKAN's default resource_display_name template helper
    function and replaces 'Unnamed resource' with 'Unnamed file'.

    '''
    display_name = helpers.resource_display_name(*args, **kwargs)
    if display_name == 'Unnamed resource':
        display_name = 'Unnamed file'
    return display_name
