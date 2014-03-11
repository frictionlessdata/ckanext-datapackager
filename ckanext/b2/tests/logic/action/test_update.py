'''Functional tests for logic/action/update.py.

'''
import nose.tools

import ckanapi

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit

import ckanext.b2.tests.helpers as custom_helpers


class TestResourceSchemaFieldUpdate(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for resource_schema_field_update.'''

    def test_resource_schema_field_update_name(self):
        '''Simple test that updating a schema field's name works.'''

        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='original-name')

        field['name'] = 'new-name'
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)
        assert field == {'index': 0, 'name': 'new-name'}

    def test_resource_schema_field_update_many(self):
        '''Test updating many field attributes at once.

        Pass all recommended params and test they all get updated correctly.

        '''
        original_attributes = {
            'name': 'original-name',
            'title': 'original-title',
            'description': 'original-description',
            'type': 'string',
            'format': 'original-format',
        }
        new_attributes = {
            'name': 'updated-name',
            'title': 'updated-title',
            'description': 'updated-description',
            'type': 'any',
            'format': 'updated-format',
        }
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, **original_attributes)

        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], index=0, **new_attributes)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)
        for key, value in new_attributes.items():
            assert field[key] == value, "Attribute wasn't updated: " + key

    def test_resource_schema_field_update_with_multiple_fields(self):
        '''Test updating a field when the schema has multiple fields.'''

        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='zero')
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='one')
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=2, name='two')

        field['name'] = 'new-name'
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=field['index'])
        assert field == {'index': 1, 'name': 'new-name'}

    def test_resource_schema_field_update_return_value(self):
        '''resource_schema_field_update should return the updated field.'''

        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='name', title='title',
            description='description', type='string', format='format')

        field = helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], index=0, name='new-name',
            title='new-title', description='new-description', type='string',
            format='format')

        assert field == helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)

    def test_resource_schema_field_update_with_custom_attributes(self):
        '''Test updating custom attributes.'''

        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='original-name',
            title='original-title', custom_attr_1='foo', custom_attr_2='bar')

        field = helpers.call_action('resource_schema_field_show',
                                    resource_id=resource['id'], index=0)
        field['custom_attr_1'] = 'foo2'
        field['custom_attr_2'] = 'bar2'
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)
        assert field['custom_attr_1'] == 'foo2'
        assert field['custom_attr_2'] == 'bar2'

    def test_resource_schema_field_update_add_attributes(self):
        '''It should be possible to add new attributes to a field by updating
        the field.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='name')

        field['title'] = 'title'
        field['custom_attr'] = 'custom'
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)
        assert field.get('title') == 'title'
        assert field.get('custom_attr') == 'custom'

    def test_resource_shema_field_update_remove_attributes(self):
        '''It should be possible to remove attributes from a field by updating
        the field.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='name', title='title',
            custom_attr='custom')

        del field['title']
        del field['custom_attr']
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)
        assert 'title' not in field
        assert 'custom_attr' not in field

    def test_resource_schema_field_update_with_duplicate_name(self):
        '''Updating a field's name to one that already exists should give a
        ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='bar')

        field['name'] = 'foo'
        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', resource_id=resource['id'],
            **field)

    def test_resource_schema_field_update_with_duplicate_index(self):
        '''Updating a field with the same index as an existing field should
        raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='bar')

        field['index'] = 0
        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', resource_id=resource['id'],
            **field)

    def test_resource_schema_field_update_with_no_index(self):
        '''Updating a field with no index should raise ValidationError.'''

        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        del field['index']
        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', resource_id=resource['id'],
            **field)

    def test_resource_schema_field_update_with_nonexistent_index(self):
        '''Updating a field with an index that doesn't exist in the resource's
        schema should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=1, name='bar')

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', resource_id=resource['id'],
            index=6, name='foobar')

    def test_resource_schema_field_update_with_no_name(self):
        '''Updating a field with no index should raise ValidationError.'''

        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        del field['name']
        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', resource_id=resource['id'],
            **field)

    def test_resource_schema_field_update_with_no_resource_id(self):
        '''Updating a field with no resource_id should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', **field)

    def test_resource_schema_field_update_with_empty_name(self):
        '''Updating a field to an empty name should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        field['name'] = ''
        nose.tools.assert_raises(toolkit.ValidationError, helpers.call_action,
            'resource_schema_field_update', resource_id=resource['id'],
            **field)

    def test_resource_schema_field_update_with_invalid_index(self):
        '''Updating a field with an invalid index should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        for index in (-1, 'foo', [], {}, '', [1,2,3], {'foo': 'bar'}):
            field['index'] = index
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_update',
                resource_id=resource['id'], **field)

    def test_resource_schema_field_update_with_invalid_resource_id(self):
        '''Updating a field with an invalid resource ID should raise
        ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        field['name'] = 'new-name'
        for resource_id in ([], {}, '', [1, 2, 3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_update',
                resource_id=resource_id, index=field['index'])

    def test_resource_schema_field_update_with_nonexistent_resource_id(self):
        '''Updating a field with a resource ID that doesn't exist should raise
        ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo')

        field['name'] = 'new-name'
        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_update',
            resource_id='abcdefghijklmnopq', index=field['index'])

    def test_resource_schema_field_update_with_invalid_type(self):
        '''Updating a field with an invalid type should raise ValidationError.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo', type='string')

        for type_ in (False, 1, 2.0, [], {}, '', 'foo', [1,2,3],
                      {'foo': 'bar'}):
            field['type'] = type_
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_update',
                resource_id=resource['id'], **field)

    def test_resource_schema_field_update_non_string_custom_attribute(self):
        '''Non-string custom attribute values should be converted to strings.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo', type='string')

        field['custom_attr_1'] = 145
        field['custom_attr_2'] = True
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=field['index'])
        assert field.get('custom_attr_1') == '145'
        assert field.get('custom_attr_2') == 'True'

    def test_resource_schema_field_update_does_not_affect_other_fields(self):
        '''Updating a resource schema field should not affect any of the
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
        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='foo', title='bar')

        field['name'] = 'bar'
        field['title'] = 'foo'
        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], **field)

        resource = helpers.call_action('resource_show', id=resource['id'])
        for key, value in resource_fields.items():
            assert resource[key] == value, (key, value)

    def test_resource_schema_field_update_with_string_int_as_index(self):
        '''If an integer in a string (like "1") is passed as the index
        parameter to resource_schema_field_update it should be converted to
        an int and used.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='original-name')

        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], index='0', name='new-name')

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)
        assert field['index'] == 0
        assert field['name'] == 'new-name'

    def test_resource_schema_field_update_with_nonconsecutive_indices(self):
        '''Test updating a field with index 3, when no fields with indexes
        0, 1 or 2 exist yet.

        '''
        resource = factories.Resource(dataset=factories.Dataset())
        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=3, name='original-name')

        helpers.call_action('resource_schema_field_update',
            resource_id=resource['id'], index=3, name='new-name')

        field = helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=3)
        assert field['index'] == 3
        assert field['name'] == 'new-name'


class TestResourceUpdate(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for resource_update.

    Tests this extension's custom resource_update schema.

    '''
    def test_resource_update_to_empty_name(self):
        '''If a user updates a resource and sets its name field to empty, the
        name should be changed to the name of the resource's uploaded file.

        '''
        user = factories.User()
        dataset = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            name='test-resource',
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        assert resource['name'] == 'test-resource'  # Just to be sure.

        resource['name'] = ''
        helpers.call_action('resource_update', **resource)

        resource = helpers.call_action('resource_show', id=resource['id'])
        assert resource['name'] == 'AllstarFull.csv'

    def test_resource_update_with_missing_name(self):
        '''If a user updates a resource and does not pass a name field, the
        name should be changed to the name of the resource's uploaded file.

        '''
        user = factories.User()
        dataset = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            name='test-resource',
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))

        del resource['name']
        helpers.call_action('resource_update', **resource)

        resource = helpers.call_action('resource_show', id=resource['id'])
        assert resource['name'] == 'AllstarFull.csv'

    def test_resource_update_to_duplicate_name(self):
        user = factories.User()
        dataset = factories.Dataset(user=user)
        resource_1 = factories.Resource(dataset=dataset)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource_2 = api.action.resource_create(package_id=dataset['id'],
            name='test-resource',
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))

        resource_2['name'] = resource_1['name']
        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_update', **resource_2)

    def test_resource_update_to_good_name(self):
        user = factories.User()
        dataset = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            name='test-resource',
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))

        resource['name'] = 'new-name'
        helpers.call_action('resource_update', **resource)

        resource = helpers.call_action('resource_show', id=resource['id'])
        assert resource['name'] == 'new-name'

    def test_resource_update_to_url(self):
        user = factories.User()
        dataset = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        original_name = resource['name']

        resource['url'] = 'http://example-resource.com/foo.csv'
        helpers.call_action('resource_update', **resource)

        resource = helpers.call_action('resource_show', id=resource['id'])
        assert resource['name'] == original_name

    def test_resource_update_with_no_format(self):
        '''If no format is given when updating a resource, the resource's
        format should not be changed.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        resource = api.action.resource_show(id=resource['id'])
        old_format = resource['format']

        resource['name'] = 'new-name'
        del resource['format']
        resource = api.action.resource_update(**resource)

        resource = api.action.resource_show(id=resource['id'])
        assert resource['format'] == old_format

    def test_resource_update_with_empty_format(self):
        '''If an empty format is given when updating a resource, the resource's
        format should not be changed.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        old_format = api.action.resource_show(id=resource['id'])['format']

        for format_ in ('', ' '):
            api.action.resource_update(id=resource['id'], format=format_,
                url=resource['url'])

            resource = api.action.resource_show(id=resource['id'])
            assert resource['format'] == old_format

    def test_resource_update_with_custom_format(self):
        '''If a format other than CSV is given when updating a resource, it
        should be accepted.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))

        for format_ in ('jpeg', 'image/png', 'foobar'):
            resource = api.action.resource_update(id=resource['id'],
                format=format_, url=resource['url'])

            resource = api.action.resource_show(id=resource['id'])
            assert resource['format'] == format_
