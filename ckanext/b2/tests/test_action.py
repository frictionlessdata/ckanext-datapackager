'''Functional tests for action.py.

'''
import os.path

import pylons.config as config
import webtest
import ckanapi
import ckan.new_tests.helpers as test_helpers
import ckan.new_tests.factories as factories
import ckan.config.middleware


def _load_plugin(plugin):
    '''Add the given plugin to the ckan.plugins config setting.

    If the given plugin is already in the ckan.plugins setting, it won't be
    added a second time.

    :param plugin: the plugin to add, e.g. ``datastore``
    :type plugin: string

    '''
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.add(plugin.strip())
    config['ckan.plugins'] = ' '.join(plugins)


def _unload_plugin(plugin):
    '''Remove the given plugin from the ckan.plugins config setting.

    If the given plugin is not in the ckan.plugins setting, nothing will be
    changed.

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


def _get_test_app():
    '''Return a webtest.TestApp for CKAN, with legacy templates disabled.

    '''
    config['ckan.legacy_templates'] = False
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


class TestAction(object):

    @classmethod
    def setup_class(cls):
        cls.original_config = config.copy()
        test_helpers.reset_db()
        _load_plugin('b2')
        cls.app = _get_test_app()

    def setup(self):
        import ckan.model as model
        model.repo.rebuild_db()

    @classmethod
    def teardown_class(cls):
        # Restore the Pylons config to its original values, in case any tests
        # changed any config settings.
        config.clear()
        config.update(cls.original_config)


    def test_resource_create(self):
        '''Test that a schema is added to a resource when it's created.

        Unit tests elsewhere test that the schemas inferred from CSV files are
        correct, here we're just testing that the schema gets added to the
        resource on resource_create().

        '''
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)

        test_site = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        # Get the CSV file to upload.
        path = 'test-data/lahmans-baseball-database/AllstarFull.csv'
        path = os.path.join(os.path.split(__file__)[0], path)
        abspath = os.path.abspath(path)
        csv_file = open(abspath)

        test_site.action.resource_create(package_id=package['id'],
                                         upload=csv_file)

        # Apparently resource_create doesn't return the resource dict when
        # called via ckanapi, so we need another call to get it.
        package = test_site.action.package_show(id=package['id'])
        # The package should have just one resource, the one we just created.
        assert len(package['resources']) == 1
        resource = package['resources'][0]

        assert 'schema' in resource
        assert 'fields' in resource['schema']
