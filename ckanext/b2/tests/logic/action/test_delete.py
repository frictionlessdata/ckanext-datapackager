'''Functional tests for logic/action/delete.py.

'''
import json

import nose.tools

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckanext.b2.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit


class TestDelete(custom_helpers.FunctionalTestBaseClass):

    def test_resource_schema_field_delete(self):
        '''Test deleting a field from a resource schema.'''

        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='one')
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=2, name='two')

        helpers.call_action('resource_schema_field_delete',
            resource_id=resource['id'], index=1)

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        fields = schema['fields']
        assert len(fields) == 2
        assert len([field for field in fields if field['index'] == 1]) == 0
        assert len([field for field in fields if field['name'] == 'one']) == 0

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_show', resource_id=resource['id'],
            index=1)

    def test_resource_schema_field_delete_last_field(self):
        '''Test deleting the last field from a resource schema.'''

        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')

        helpers.call_action('resource_schema_field_delete',
            resource_id=resource['id'], index=0)

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        fields = schema['fields']
        assert len(fields) == 0

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_show', resource_id=resource['id'],
            index=0)

    def test_resource_schema_field_delete_with_invalid_index(self):
        '''Deleting a field with an invalid index should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')


        for index in (-1, 'foo', [], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_delete',
                resource_id=resource['id'], index=index)

    def test_resource_schema_field_delete_with_nonexistent_index(self):
        '''Deleting a field with an index that doesn't exist should raise
        ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')


        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_delete',
            resource_id=resource['id'], index=9)

    def test_resource_shema_field_delete_with_multiple_matching_indices(self):
        '''Deleting a field with an index that matches more than one field in
        the resource's schema should raise ValidationError.

        '''
        # resource_schema_field_create() won't let us create two fields with
        # the same index, but we can create them by passing the schema to
        # resource_create directly.
        schema = {
            'fields': [
                {'name': 'foo', 'index': 3},
                {'name': 'bar', 'index': 3},
            ],
        }
        resource = factories.Resource(dataset=factories.Dataset(),
            schema=json.dumps(schema))

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_delete',
            resource_id=resource['id'], index=3)

    def test_resource_schema_field_delete_with_invalid_resource_id(self):
        '''Deleting a field with an invalid resource ID should raise
        ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')

        for resource_id in ([], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_delete',
                resource_id=resource_id, index=0)

    def test_resource_schema_field_delete_with_nonexistent_resource_id(self):
        '''Deleting a field with a resource ID that doesn't exist should raise
        ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_delete',
            resource_id='abcdefghijklmnopqrst', index=0)

    def test_resource_schema_field_delete_with_no_index(self):
        '''Deleting a field with no index should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_delete',
            resource_id=resource['id'])

    def test_resource_schema_field_delete_with_no_resource_id(self):
        '''Deleting a field with no resource ID should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_delete', index=0)

    def test_resource_schema_field_delete_extra_params(self):
        '''Unknown params passed to resource_schema_field_delete should be
        ignored, the resource should still be deleted as long as the correct
        resource_id and index are given.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='one')
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=2, name='two')

        helpers.call_action('resource_schema_field_delete',
            resource_id=resource['id'], index=1, foo='foo', bar='bar')

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        fields = schema['fields']
        assert len(fields) == 2
        assert len([field for field in fields if field['index'] == 1]) == 0
        assert len([field for field in fields if field['name'] == 'one']) == 0

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_show', resource_id=resource['id'],
            index=1)
