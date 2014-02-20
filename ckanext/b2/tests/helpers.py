'''Test helper functions and classes.'''

import ckan.config.middleware
import pylons.config as config
import webtest


def get_test_app():
    '''Return a webtest.TestApp for CKAN, with legacy templates disabled.

    For functional tests that need to request CKAN pages or post to the API.
    Unit tests shouldn't need this.

    '''
    config['ckan.legacy_templates'] = False
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


def load_plugin(plugin):
    '''Add the given plugin to the ckan.plugins config setting.

    This is for functional tests that need the plugin to be loaded.
    Unit tests shouldn't need this.

    If the given plugin is already in the ckan.plugins setting, it won't be
    added a second time.

    :param plugin: the plugin to add, e.g. ``datastore``
    :type plugin: string

    '''
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.add(plugin.strip())
    config['ckan.plugins'] = ' '.join(plugins)


def unload_plugin(plugin):
    '''Remove the given plugin from the ckan.plugins config setting.

    If the given plugin is not in the ckan.plugins setting, nothing will be
    changed.

    This is for functional tests that need the plugin to be loaded.
    Unit tests shouldn't need this.

    :param plugin: the plugin to remove, e.g. ``datastore``
    :type plugin: string

    '''
    plugins = set(config['ckan.plugins'].strip().split())
    try:
        plugins.remove(plugin.strip())
    except KeyError:
        # Looks like the plugin was not in ckan.plugins.
        pass
    config['ckan.plugins'] = ' '.join(plugins)


class FunctionalTestBaseClass(object):
    '''A base class for functional test classes to inherit from.

    If you're overriding methods that this class provides, like setup_class()
    and teardown_class(), make sure to use super() to call this class's methods
    at the top of yours!

    '''
    @classmethod
    def setup_class(cls):
        # Make a copy of the Pylons config, so we can restore it in teardown.
        cls.original_config = config.copy()

    @classmethod
    def teardown_class(cls):
        # Restore the Pylons config to its original values, in case any tests
        # changed any config settings.
        config.clear()
        config.update(cls.original_config)
