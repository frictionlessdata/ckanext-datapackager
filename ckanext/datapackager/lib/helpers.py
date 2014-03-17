'''Some custom template helper functions.

'''
import ckan.lib.helpers as helpers
import ckan.model as model
import ckan.plugins.toolkit as toolkit


def resource_display_name(*args, **kwargs):
    '''Return a display name for the given resource.

    This overrides CKAN's default resource_display_name template helper
    function and replaces 'Unnamed resource' with 'Unnamed file'.

    '''
    display_name = helpers.resource_display_name(*args, **kwargs)
    if display_name == 'Unnamed resource':
        display_name = 'Unnamed file'
    return display_name


def get_resource_schema(resource_id):
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    schema_show = toolkit.get_action('resource_schema_show')
    return schema_show(context, {'resource_id': resource_id})


def get_resource_schema_field(resource_id, index):
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    schema_field_show = toolkit.get_action('resource_schema_field_show')
    data_dict = {'resource_id': resource_id, 'index': index}
    return schema_field_show(context, data_dict)

def get_resource(resource_id):

    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    resource_show = toolkit.get_action('resource_show')
    return resource_show(context,{'id': resource_id})
