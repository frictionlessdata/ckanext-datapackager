'''Functional tests for logic/action/create.py.

'''
import os

import nose.tools

import ckanapi

import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit

import ckanext.datapackager.tests.helpers as custom_helpers


class TestResourceSchemaFieldCreate(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for resource_schema_field_create.'''

    def test_resource_schema_field_create_simple(self):
        '''Simple test that creating a schema field works.

        Simple test of resource_schema_field_create passing only resource_id,
        index and name.

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

    def test_resource_schema_field_create_return_value(self):
        '''resource_schema_field_create should return the field that was
        created.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        field = helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=0, name='name', title='title',
            description='description', type='string', format='format')

        assert field == helpers.call_action('resource_schema_field_show',
            resource_id=resource['id'], index=0)

    def test_resource_schema_field_create_with_custom_attributes(self):
        '''Test that custom schema field attributes are saved correctly.'''

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

        for index in (-1, 'foo', [], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_create',
                index=index, name='name', resource_id=resource['id'])

    def test_resource_schema_field_create_with_invalid_resource_id(self):
        '''Creating a field with an invalid resource ID should raise
        ValidationError.

        '''
        factories.Resource(dataset=factories.Dataset())

        for resource_id in ([], {}, '', [1,2,3], {'foo': 'bar'}):
            nose.tools.assert_raises(toolkit.ValidationError,
                helpers.call_action, 'resource_schema_field_create',
                resource_id=resource_id, index=0)

    def test_resource_schema_field_create_with_nonexistent_resource_id(self):
        '''Creating a field with a resource ID that doesn't exist should raise
        ValidationError.

        '''
        factories.Resource(dataset=factories.Dataset())

        nose.tools.assert_raises(toolkit.ValidationError,
            helpers.call_action, 'resource_schema_field_create',
            resource_id='abcdefghijklmnopqrst', index=0)

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

        for type_ in (False, 1, 2.0, [], {}, '', 'foo', [1,2,3],
                      {'foo': 'bar'}):
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

    def test_resource_schema_field_create_with_string_int_as_index(self):
        '''If an integer in a string (like "1") is passed as the index
        parameter to resource_schema_field_create it should be converted to
        an int and used.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index='0', name='foo')

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field == {'index': 0, 'name': 'foo'}

    def test_resource_schema_field_create_with_nonconsecutive_indices(self):
        '''Test creating a field with index 3, when no fields with indexes
        0, 1 or 2 exist yet.

        '''
        resource = factories.Resource(dataset=factories.Dataset())

        helpers.call_action('resource_schema_field_create',
            resource_id=resource['id'], index=3, name='foo')

        schema = helpers.call_action('resource_schema_show',
            resource_id=resource['id'])
        assert 'fields' in schema
        fields = schema['fields']
        assert len(fields) == 1
        field = fields[0]
        assert field == {'index': 3, 'name': 'foo'}


class TestResourceCreate(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for resource_create.

    Tests for this plugin's custom resource_create schema.

    '''
    def test_resource_create_with_no_name(self):
        '''If you create a new resource and upload a data file but don't give
        a name for the resource, the resource name should be set to the name
        of the data file.

        '''
        user = factories.User()
        package = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        csv_file = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        resource = api.action.resource_create(package_id=package['id'],
                                              upload=csv_file)

        resource = api.action.resource_show(id=resource['id'])
        assert resource['name'] == 'AllstarFull.csv', resource['name']


    def test_resource_create_upload_same_file_with_no_name(self):
        '''If you create multiple resources, uploading files with the same name
        and not giving names for the resources, the resource names should be
        set to the file name but with _2, _3, etc. appended.

        '''
        user = factories.User()
        package = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        resource_1 = api.action.resource_create(package_id=package['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        resource_2 = api.action.resource_create(package_id=package['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        resource_3 = api.action.resource_create(package_id=package['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))
        assert resource_1['name'] == 'AllstarFull.csv', resource_1['name']
        assert resource_2['name'] == 'AllstarFull_2.csv', resource_2['name']
        assert resource_3['name'] == 'AllstarFull_3.csv', resource_3['name']

    def test_resource_create_with_duplicate_resource_name(self):
        '''resource_create() should raise ValidationError if you call it and
        manually specify a duplicate resource name.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource_1 = factories.Resource(dataset=dataset, name='foo')

        # Using `with assert_raises(...) as context` like this does not work
        # in Python 2.6.
        with nose.tools.assert_raises(toolkit.ValidationError) as context:
            api.action.resource_create(package_id=dataset['id'], url='foo',
                name=resource_1['name'])
        assert context.exception.error_dict == {'__type': 'Validation Error',
            'name': [
                "A data package can't contain two files with the same name"]}

    def test_resource_create_with_custom_name(self):
        '''If you create a resource and given a unique custom name, that name
        should be taken as the resource's name.

        '''
        user = factories.User()
        dataset = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        resource = api.action.resource_create(package_id=dataset['id'],
            name='test-resource',
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))

        assert resource['name'] == 'test-resource'

    def test_resource_create_with_url(self):
        '''If you create a resource giving a URL instead of uploading a file,
        and not specifying a resource name, the filename should be extracted
        from the URL.

        '''
        user = factories.User()
        package = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        resource = api.action.resource_create(package_id=package['id'],
            url='http://example.com/resources/foo.csv')

        resource = api.action.resource_show(id=resource['id'])
        assert resource['name'] == 'foo.csv'

    def test_resource_create_url_with_trailing_slash(self):

        user = factories.User()
        package = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        resource = api.action.resource_create(package_id=package['id'],
            url='http://example.com/resources/')

        resource = api.action.resource_show(id=resource['id'])
        assert resource['name'] == 'resources'

    def test_resource_create_url_with_no_path(self):

        user = factories.User()
        package = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        resource = api.action.resource_create(package_id=package['id'],
            url='http://example.com')

        resource = api.action.resource_show(id=resource['id'])
        assert resource['name'] == 'example.com'

    def test_resource_create_with_no_format(self):
        '''If no format is given when creating a resource, the resource's
        format should be set to CSV.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        resource = api.action.resource_create(package_id=dataset['id'],
            upload=custom_helpers.get_csv_file(
                'test-data/lahmans-baseball-database/AllstarFull.csv'))

        resource = api.action.resource_show(id=resource['id'])
        assert resource['format'] == 'CSV'

    def test_resource_create_with_empty_format(self):
        '''If an empty format is given when creating a resource, the resource's
        format should be set to CSV.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        for format_ in ('', ' '):
            resource = api.action.resource_create(package_id=dataset['id'],
                format=format_,
                upload=custom_helpers.get_csv_file(
                    'test-data/lahmans-baseball-database/AllstarFull.csv'))

            resource = api.action.resource_show(id=resource['id'])
            assert resource['format'] == 'CSV', resource['format']

    def test_resource_create_with_custom_format(self):
        '''If a format other than CSV is given when creating a resource, it
        should be accepted.

        '''
        user = factories.User()
        dataset = factories.Dataset()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])

        for format_ in ('jpeg', 'image/png', 'foobar'):
            resource = api.action.resource_create(package_id=dataset['id'],
                format=format_,
                upload=custom_helpers.get_csv_file(
                    'test-data/lahmans-baseball-database/AllstarFull.csv'))

            resource = api.action.resource_show(id=resource['id'])
            assert resource['format'] == format_


class TestResourceSchemaPKeyCreate(custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for resource_schema_pkey_create.'''

    def _create_resources(self):
        resource = factories.Resource(dataset=factories.Dataset())
        api = ckanapi.TestAppCKAN(self.app, apikey=factories.User()['apikey'])
        api.action.resource_schema_field_create(resource_id=resource['id'],
            index=0, name='foo')
        api.action.resource_schema_field_create(resource_id=resource['id'],
            index=1, name='bar')
        return resource, api

    def test_resource_schema_pkey_create_string(self):

        resource, api = self._create_resources()

        result = api.action.resource_schema_pkey_create(
            resource_id=resource['id'], pkey='foo')

        schema = api.action.resource_schema_show(resource_id=resource['id'])
        assert schema['primaryKey'] == 'foo'
        assert result == 'foo', ("resource_schema_pkey_create should return "
            "the created primary key")


    def test_resource_schema_pkey_create_list(self):

        resource, api = self._create_resources()

        pkey = ['foo', 'bar']
        result = api.action.resource_schema_pkey_create(
            resource_id=resource['id'], pkey=pkey)

        schema = api.action.resource_schema_show(resource_id=resource['id'])
        assert schema['primaryKey'] == pkey
        assert result == pkey, ("resource_schema_pkey_create should return "
            "the created primary key")

    def test_resource_schema_pkey_create_string_with_nonexistent_name(self):

        resource, api = self._create_resources()

        nose.tools.assert_raises(toolkit.ValidationError,
            api.action.resource_schema_pkey_create, resource_id=resource['id'],
            pkey='does-not-exist')

    def test_resource_schema_pkey_create_list_with_nonexistent_name(self):

        resource, api = self._create_resources()

        nose.tools.assert_raises(toolkit.ValidationError,
            api.action.resource_schema_pkey_create, resource_id=resource['id'],
            pkey=['foo', 'bar', 'does-not-exist'])

    def test_resource_schema_pkey_create_with_invalid_primary_key(self):

        resource, api = self._create_resources()

        for key in (None, -1, 0.23, 59, True, False, '', ' ', [], {},
                    [None, -1, 0.23, 59, True, False, '', ' ']):
            nose.tools.assert_raises(toolkit.ValidationError,
                api.action.resource_schema_pkey_create,
                resource_id=resource['id'], pkey=key)

    def test_resource_schema_pkey_create_with_missing_primary_key(self):

        resource, api = self._create_resources()

        nose.tools.assert_raises(toolkit.ValidationError,
            api.action.resource_schema_pkey_create, resource_id=resource['id'])

    def test_resource_schema_pkey_create_with_invalid_resource_id(self):

        resource, api = self._create_resources()

        for resource_id in ([], {}, '', [1,2,3], {'foo': 'bar'}, 'abcdefghij'):
            nose.tools.assert_raises(toolkit.ValidationError,
                api.action.resource_schema_pkey_create,
                resource_id=resource_id, pkey='foo')

    def test_resource_schema_pkey_create_with_missing_resource_id(self):

        resource, api = self._create_resources()

        nose.tools.assert_raises(toolkit.ValidationError,
            api.action.resource_schema_pkey_create, pkey='foo')

    def test_resource_schema_pkey_create_with_nonexistent_resource_id(self):

        resource, api = self._create_resources()

        nose.tools.assert_raises(toolkit.ValidationError,
            api.action.resource_schema_pkey_create,
            resource_id='does-not-exist', pkey='foo')

    def test_resource_schema_pkey_create_when_primary_key_already_exists(self):
        resource, api = self._create_resources()
        api.action.resource_schema_pkey_create(resource_id=resource['id'],
            pkey='foo')

        nose.tools.assert_raises(toolkit.ValidationError,
            api.action.resource_schema_pkey_create,
            resource_id=resource['id'], pkey='bar')

    # TODO
    #def test_resource_schema_pkey_create_with_nonunique_primary_key(self):
        #raise NotImplementedError
