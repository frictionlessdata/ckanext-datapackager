'''Functional tests for plugin.py.

'''
import os.path

import ckanapi
import ckan.new_tests.factories as factories
import ckanext.b2.tests.helpers as custom_helpers


def _get_csv_file(relative_path):
        path = os.path.join(os.path.split(__file__)[0], relative_path)
        abspath = os.path.abspath(path)
        csv_file = open(abspath)
        return csv_file


class TestPlugin(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for B2Plugin.

    '''
    def setup(self):
        import ckan.model as model
        model.repo.rebuild_db()

    def test_resource_create(self):
        '''Test that a schema is added to a resource when it's created.

        Unit tests elsewhere test that the schemas inferred from CSV files are
        correct, here we're just testing that the schema gets added to the
        resource on resource_create().

        '''
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        csv_file = _get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')

        api.action.resource_create(package_id=package['id'],
                                         upload=csv_file)

        # Apparently resource_create doesn't return the resource dict when
        # called via ckanapi, so we need another call to get it.
        package = api.action.package_show(id=package['id'])

        # The package should have just one resource, the one we just created.
        assert len(package['resources']) == 1
        resource = package['resources'][0]

        # There should be a schema in the resource.
        assert 'schema' in resource
        assert 'fields' in resource['schema']

    def test_resource_update(self):
        '''Test that a resource's schema is updated when the resource is
        updated with a new uploaded CSV file.

        Unit tests elsewhere test that the schemas inferred from CSV files are
        correct, here we're just testing that the schema gets added to the
        resource on resource_create().

        '''
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        # Upload a first CSV file to the package.
        csv_file = _get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        api.action.resource_create(package_id=package['id'], upload=csv_file)

        # Get the generated schema from the resource.
        package = api.action.package_show(id=package['id'])
        assert len(package['resources']) == 1
        resource = package['resources'][0]
        assert 'schema' in resource
        original_schema = resource['schema']

        # Now update the resource with a new file.
        csv_file = _get_csv_file(
            'test-data/lahmans-baseball-database/Appearances.csv')
        api.action.resource_update(id=resource['id'], upload=csv_file)

        # Check that the schema has been changed.
        package = api.action.package_show(id=package['id'])
        assert len(package['resources']) == 1
        resource = package['resources'][0]
        assert 'schema' in resource
        schema = resource['schema']
        assert 'fields' in schema
        assert schema != original_schema
