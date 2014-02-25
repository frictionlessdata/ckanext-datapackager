'''Schemas used by this extension to validate and convert data coming from the
user or coming from the database.

'''
import ckan.lib.navl.validators as navl_validators
import ckan.logic.validators as core_validators
import ckanext.b2.logic.validators as custom_validators


def resource_schema_field_create_schema():  # Yes, it says schema twice.

    return {
        'resource_id': [navl_validators.not_empty, unicode],
        'name': [navl_validators.not_empty, unicode,
                 custom_validators.field_name_validator],
        'title': [navl_validators.ignore_missing, unicode],
        'description': [navl_validators.ignore_missing, unicode],
        'type': [navl_validators.ignore_missing,
                 custom_validators.field_type_validator],
        'format': [navl_validators.ignore_missing, unicode],
        '__extras': [navl_validators.ignore_missing,
                     core_validators.extras_unicode_convert,
                     navl_validators.keep_extras],
    }
