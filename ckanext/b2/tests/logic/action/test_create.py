'''Functional tests for logic/action/create.py.

'''
import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckanext.b2.tests.helpers as custom_helpers


class TestCreate(custom_helpers.FunctionalTestBaseClass):

    def test_resource_schema_field_create(self):
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], name='foo')

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field == {'name': 'foo'}
