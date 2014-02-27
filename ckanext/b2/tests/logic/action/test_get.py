'''Functional tests for logic/action/get.py.

'''
import nose.tools

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckanext.b2.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit


def _create_resource_and_field():
        resource = factories.Resource(dataset=factories.Dataset())
        field = {
            'index': 0,
            'name': 'name',
            'title': 'title',
            'foo': 'bar'
        }
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], **field)
        return resource, field


class TestGet(custom_helpers.FunctionalTestBaseClass):

    def test_resource_schema_show(self):
        '''resource_schema_show should return the resource's schema.'''

        resource, field = _create_resource_and_field()

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])

        assert schema == {'fields': [field]}

    def test_resource_schema_show_with_invalid_resource_id(self):
        '''resource_schema_show should raise ValidationError if called with an
        invalid resource_id.

        '''
        _create_resource_and_field()

        for resource_id in ([], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_show',
                resource_id=resource_id)

    def test_resource_schema_show_with_nonexistent_resource_id(self):
        '''resource_schema_show should raise ValidationError if called with a
        resource_id that doesn't exist.

        '''
        _create_resource_and_field()

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_show',
            resource_id='abcdefghijklmnop')

    def test_resource_schema_show_with_missing_resource_id(self):
        '''resource_schema_show should raise ValidationError if called without
        a resource_id argument.

        '''
        _create_resource_and_field()

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_show')

    def test_resource_schema_show_with_extra_args(self):
        '''resource_schema_show should ignore any unknown arguments that are
        passed to it, it should still return the schema as long as it's given
        a valid resource_id.

        '''
        resource, field = _create_resource_and_field()

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'], foo='foo', bar='bar')

        assert schema == {'fields': [field]}

    def test_resource_schema_field_show(self):
        '''resource_schema_field_show should return the field'''

        resource, field = _create_resource_and_field()

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=field['index'])

        assert field == field

    def test_resource_schema_field_show_with_invalid_resource_id(self):
        '''resource_schema_field_show should raise ValidationError if called
        with an invalid resource_id.'''

        _, field = _create_resource_and_field()

        for resource_id in ([], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_show',
                resource_id=resource_id, index=field['index'])

    def test_resource_schema_field_show_with_nonexistent_resource_id(self):
        '''resource_schema_field_show should raise ValidationError if called
        with a resource_id that doesn't exist.

        '''
        _, field = _create_resource_and_field()

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_show',
            resource_id='abcdefghijklmnop', index=field['index'])

    def test_resource_schema_field_show_with_missing_resource_id(self):
        '''resource_schema_field_show should raise ValidationError if called
        without a resource_id.

        '''
        _, field = _create_resource_and_field()

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_show',
            index=field['index'])

    def test_resource_schema_field_show_with_invalid_index(self):
        '''resource_schema_field_show should raise ValidationError if called
        with an invalid index.

        '''
        resource, _ = _create_resource_and_field()

        for index in (-1, 'foo', [], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_show',
                resource_id=resource['id'], index=index)

    def test_resource_schema_field_show_with_nonexistent_index(self):
        '''resource_schema_field_show should raise ValidationError if called
        with a field index that doesn't exist in the given resource's schema.

        '''
        resource, field = _create_resource_and_field()

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_show',
            resource_id=resource['id'], index=5)

    def test_resource_schema_field_show_with_missing_index(self):
        '''resource_schema_field_show should raise ValidationError if called
        without an index.

        '''
        resource, _ = _create_resource_and_field()

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_show',
            resource_id=resource['id'])

    def test_resource_schema_field_show_with_extra_args(self):
        '''resource_schema_field_show should ignore any unknown arguments that
        are passed to it, it should still return the field as long as it's
        given a valid resource_id and index.

        '''
        resource, field = _create_resource_and_field()

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=field['index'],
            foo='foo', bar='bar')

        assert field == field
