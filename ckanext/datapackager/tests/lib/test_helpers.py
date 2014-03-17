'''Unit tests for lib/helpers.py.

'''
import ckanext.datapackager.lib.helpers as helpers


def test_resource_display_name():
    '''Test that resource_display_name() changes "Unnamed resource" to
    "Unnamed file".

    '''
    resource_dict = {
        'name': None,
        'description': None
    }

    display_name = helpers.resource_display_name(resource_dict)

    assert display_name == "Unnamed file"
