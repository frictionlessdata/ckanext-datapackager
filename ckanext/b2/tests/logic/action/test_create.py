'''Functional tests for action/create.py.

'''
import os.path

import ckanapi
import ckan.new_tests.factories as factories
import ckanext.b2.tests.helpers as custom_helpers


class TestCreate(custom_helpers.FunctionalTestBaseClass):

    @classmethod
    def setup_class(cls):
        super(TestCreate, cls).setup_class()
        custom_helpers.load_plugin('b2')
        cls.app = custom_helpers.get_test_app()

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
        path = '../../test-data/lahmans-baseball-database/AllstarFull.csv'
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
