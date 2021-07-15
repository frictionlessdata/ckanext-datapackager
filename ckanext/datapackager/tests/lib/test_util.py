import os

import nose.tools
import ckanapi as ckanapi
import pytest

import ckan.tests.factories as factories

import ckanext.datapackager.lib.util as util
import ckanext.datapackager.tests.helpers as custom_helpers
import ckanext.datapackager.exceptions as exceptions

@pytest.mark.ckan_config('ckan.plugins', 'datapackager')
@pytest.mark.usefixtures('clean_db', 'with_plugins', 'with_request_context')
class TestResourceSchemaFieldCreate():

    def test_get_path_to_resource_file_with_uploaded_file(self, app):

        user = factories.User()
        package = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(app, apikey=user['apikey'])
        csv_file = custom_helpers.get_csv_file('datetimes.csv')
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=csv_file,
            url=''  # FIXME: See https://github.com/ckan/ckan/issues/2769
        )

        path = util.get_path_to_resource_file(resource)

        # Check that the path is correct by comparing the contents of the
        # uploaded copy of the file to the original file.
        assert open(path).read() == (
            open(os.path.join(os.path.split(__file__)[0],
                '../test-data/datetimes.csv')).read())

    def test_get_path_to_resource_file_with_linked_file(self):

        resource = factories.Resource(dataset=factories.Dataset(),
                                      url='http://example.com/foo.csv')

        nose.tools.assert_raises(exceptions.ResourceFileDoesNotExistException,
            util.get_path_to_resource_file, resource)
