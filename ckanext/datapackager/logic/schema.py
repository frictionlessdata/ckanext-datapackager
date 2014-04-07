'''Schemas used by this extension to validate and convert data coming from the
user or coming from the database.

'''
import ckan.lib.navl.validators as navl_validators
import ckan.logic.validators as core_validators
import ckanext.datapackager.logic.validators as custom_validators


def resource_schema_field_create_schema():  # Yes, it says schema twice.

    return {
        '__before': [custom_validators.resource_id_validator],
        'resource_id': [],
        'index': [navl_validators.not_missing,
                  custom_validators.create_field_index_validator],
        'name': [navl_validators.not_empty, unicode,
                 custom_validators.create_field_name_validator],
        'title': [navl_validators.ignore_missing, unicode],
        'description': [navl_validators.ignore_missing, unicode],
        'type': [navl_validators.ignore_missing,
                 custom_validators.field_type_validator],
        'format': [navl_validators.ignore_missing, unicode],
        '__extras': [navl_validators.ignore_missing,
                     core_validators.extras_unicode_convert,
                     navl_validators.keep_extras],
    }


def resource_schema_field_update_schema():

    return {
        '__before': [custom_validators.resource_id_validator],
        'resource_id': [],
        'index': [navl_validators.not_missing,
                  custom_validators.update_field_index_validator],
        'name': [navl_validators.not_empty, unicode,
                 custom_validators.update_field_name_validator],
        'title': [navl_validators.ignore_missing, unicode],
        'description': [navl_validators.ignore_missing, unicode],
        'type': [navl_validators.ignore_missing,
                 custom_validators.field_type_validator],
        'format': [navl_validators.ignore_missing, unicode],
        '__extras': [navl_validators.ignore_missing,
                     core_validators.extras_unicode_convert,
                     navl_validators.keep_extras],
    }


def resource_schema_field_delete_schema():

    return {
        '__before': [custom_validators.resource_id_validator],
        'resource_id': [],
        'index': [custom_validators.resource_id_validator,
                  navl_validators.not_missing,
                  custom_validators.update_field_index_validator],
    }


def resource_schema_field_show_schema():
    return resource_schema_field_delete_schema()


def resource_schema_show_schema():
    return {
        'resource_id': [custom_validators.resource_id_validator],
    }


def resource_schema_pkey_show_schema():
    return resource_schema_show_schema()


def resource_schema_pkey_update_schema():
    return {
        'resource_id': [custom_validators.resource_id_validator],
        'pkey': [custom_validators.primary_key_validator],
    }


def resource_schema_pkey_delete_schema():
    return {
        'resource_id': [custom_validators.resource_id_validator],
    }


def resource_schema_fkey_show_schema():
    return {
        'resource_id': [custom_validators.resource_id_validator],
    }


def resource_schema_fkey_delete_schema():
    return {
        'resource_id': [navl_validators.not_missing, custom_validators.resource_id_validator],
        'fkeys': {
            'field': [navl_validators.not_missing, custom_validators.foreign_key_field_validator],
        }
    }


def resource_schema_fkey_update_schema():
    return {
        'resource_id': [navl_validators.not_missing, custom_validators.resource_id_validator],
        'fkeys': {
            'field': [navl_validators.not_missing, custom_validators.foreign_key_field_validator],
            'referenced_resource_id': [navl_validators.not_missing, custom_validators.resource_id_validator],
            'referenced_field': [navl_validators.not_missing, custom_validators.foreign_key_reference_validator],
        }
    }
