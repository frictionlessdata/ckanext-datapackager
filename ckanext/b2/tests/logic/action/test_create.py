'''Functional tests for logic/action/create.py.

'''
import json

import nose.tools

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckanext.b2.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit


class TestCreate(custom_helpers.FunctionalTestBaseClass):

    def test_resource_schema_field_create_simple(self):
        '''Simple test that creating a schema field works.

        Simple test of resource_schema_field_create passing only resource_id
        and name.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field == {'index': 0, 'name': 'foo'}

    def test_resource_schema_field_create_complex(self):
        '''More complex test of creating a schema field.

        Pass all recommended params and test they all get created correctly.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        # The field attributes we will pass.
        name = 'test-field'
        title = 'Test Field'
        description = 'Just a simple test field.'
        type_ = 'string'
        format_ = 'foobar'

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name=name, title=title,
            description=description, type=type_, format=format_)

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field['name'] == name
        assert field['title'] == title
        assert field['description'] == description
        assert field['type'] == type_
        assert field['format'] == format_

    def test_resource_schema_field_create_with_custom_attributes(self):
        '''Test that string type custom schema field attributes are saved
        correctly.'''

        resource = factories.Resource(dataset=factories.Dataset())

        # The field attributes we will pass.
        name = 'test-field'
        title = 'Test Field'
        custom_attribute_1 = 'foo'
        custom_attribute_2 = 'bar'

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name=name, title=title,
            custom_attribute_1=custom_attribute_1,
            custom_attribute_2=custom_attribute_2)

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field['name'] == name
        assert field['title'] == title
        assert field['custom_attribute_1'] == custom_attribute_1
        assert field['custom_attribute_2'] == custom_attribute_2

    def test_resource_schema_field_create_when_schema_already_exists(self):
        '''Test creating a new schema field in a schema that already exists.

        (The tests above have been testing with resources that had no schema
        to begin with.)

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        # The field attributes we will pass.
        name = 'test-field'
        title = 'Test Field'

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name=name, title=title)

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 2
        assert fields[0]['name'] == 'foo'
        assert fields[1]['name'] == name
        assert fields[1]['title'] == title

    def test_resource_schema_field_create_when_name_already_exists(self):
        '''Creating a field with the same name as an existing field should give
        a ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_create', resource_id=resource['id'],
            index=1, name='foo')

    def test_resource_schema_field_create_with_no_index(self):
        '''Creating a field with no index should raise ValidationError.'''

        resource = factories.Resource(dataset=factories.Dataset())

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_create', name='name',
            resource_id=resource['id'])

    def test_resource_schema_field_create_with_no_name(self):
        '''Creating a field with no name should raise ValidationError.'''

        resource = factories.Resource(dataset=factories.Dataset())

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_create', index=0,
            resource_id=resource['id'])

    def test_resource_schema_field_create_with_no_resource_id(self):
        '''Creating a field with no resource_id should raise ValidationError.'''

        factories.Resource(dataset=factories.Dataset())

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_create', index=0, name='foo')

    def test_resource_schema_field_create_with_empty_name(self):
        '''Creating a field with an empty name should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_create',
            resource_id=resource['id'], index=0, name='')

    def test_resource_schema_field_create_with_invalid_index(self):
        '''Creating a field with an invalid index should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        for index in (-1, 'foo', [], {}, ''):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_create',
                index=index, name='name', resource_id=resource['id'])

    def test_resource_schema_field_create_with_duplicate_index(self):
        '''Creating a field with the same index as an existing field should
        raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_create',
            index=0, name='bar', resource_id=resource['id'])

    def test_resource_schema_field_create_with_invalid_type(self):
        '''Creating a field with an invalid type should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        for type_ in (False, 1, 2.0, [], {}, '', 'foo'):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_create',
                resource_id=resource['id'], index=0, name='foo', type=type_)

    def test_resource_schema_field_create_non_string_custom_attribute(self):
        '''Non-string custom attribute values should be converted to strings.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        # The field attributes we will pass.
        name = 'test-field'
        title = 'Test Field'
        custom_attribute_1 = 145
        custom_attribute_2 = True

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name=name, title=title,
            custom_attribute_1=custom_attribute_1,
            custom_attribute_2=custom_attribute_2)

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field['custom_attribute_1'] == '145'
        assert field['custom_attribute_2'] == 'True'

    def test_resource_schema_field_create_does_not_affect_other_fields(self):
        '''Creating a resource schema field should not affect any of the
        resource's other fields.

        '''
        resource_fields = {
            'url': 'http://www.example_resource.com',
            'description': 'Just a test resource',
            'format': 'CSV',
            'hash': 'xxx',
            'name': 'test-resource',
            'mimetype': 'text/csv',
            'size': '10',
            }
        resource = factories.Resource(dataset=factories.Dataset(),
                                      **resource_fields)

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='name', title='title',
            description='description', type='string', format='format')

        resource = helpers.call_action('resource_show', id=resource['id'])
        for key, value in resource_fields.items():
            assert resource[key] == value, (key, value)
