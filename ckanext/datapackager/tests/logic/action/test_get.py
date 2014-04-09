'''Functional tests for logic/action/get.py.

'''
import nose.tools

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckanext.datapackager.tests.helpers as custom_helpers
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

        for index in (-1, 'foo', [], {}, '', [1, 2, 3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_show',
                resource_id=resource['id'], index=index)

    def test_resource_schema_field_show_with_string_int(self):
        '''If an integer is passed to resource_schema_field_show in a string
        (like "1") it should be converted to an int and the field returned
        correctly.

        '''
        resource, field = _create_resource_and_field()

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index='0')

        assert field == field

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

    def test_resource_schema_field_show_with_nonconsecutive_indices(self):
        '''Test showing a field with index 3, when no fields with indexes
        0, 1 or 2 exist yet.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = {
            'index': 3,
            'name': 'name',
            'title': 'title',
            'foo': 'bar'
        }
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=3)

        assert field == field

    def test_resource_schema_field_show_with_out_of_order_creation(self):
        '''Test that resource_schema_field_show works even if the fields were
        not created in index order.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field_3 = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=3, name='three')
        field_1 = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='one')
        field_0 = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')
        field_2 = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=2, name='two')

        assert helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0) == field_0
        assert helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=1) == field_1
        assert helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=2) == field_2
        assert helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=3) == field_3

    def test_package_to_tabular_data_format(self):

        dataset = factories.Dataset()
        factories.Resource(dataset=dataset, url='http://test.com/test-url-1',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')
        factories.Resource(dataset=dataset, url='http://test.com/test-url-2',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        tdf = helpers.call_action('package_to_tabular_data_format',
                                  id=dataset['name'])

        expected_output = {
            'name': dataset['name'],
            'resources': [
                {
                    'schema': {
                        u'fields': [{u'name': u'col1', u'type': u'string'}]
                    },
                    'url': u'http://test.com/test-url-1'
                },
                {
                    'schema': {
                        u'fields': [{u'name': u'col1', u'type': u'string'}]
                    },
                    'url': u'http://test.com/test-url-2'
                }
            ]
        }
        nose.tools.assert_equals(expected_output, tdf)

    def test_package_to_tdf_with_missing_id(self):
        nose.tools.assert_raises(
            toolkit.ValidationError,
            helpers.call_action,
            'package_to_tabular_data_format',
        )
