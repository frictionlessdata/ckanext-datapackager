import zipstream

import pylons

from ckan.common import request
import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.base as base


class DataPackagerPackageController(toolkit.BaseController):

    def new_metadata(self, id, data=None, errors=None, error_summary=None):
        import ckan.lib.base as base

        # Change the package state from draft to active and save it.
        context = {'model': model, 'session': model.Session,
                   'user': toolkit.c.user or toolkit.c.author,
                   'auth_user_obj': toolkit.c.userobj}
        data_dict = toolkit.get_action('package_show')(context, {'id': id})
        data_dict['id'] = id
        data_dict['state'] = 'active'
        toolkit.get_action('package_update')(context, data_dict)

        base.redirect(helpers.url_for(controller='package', action='read',
                                      id=id))

    def download_tabular_data_format(self, package_id):
        '''Return the given package as a Tabular Data Format ZIP file.

        '''
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user or toolkit.c.author,
        }
        r = toolkit.response
        r.content_disposition = 'attachment; filename={0}.zip'.format(
            package_id)
        r.content_type = 'application/octet-stream'

        # Make a zipstream and put it in the context. This means the
        # package_to_tabular_data_format action will add files into 
        # the zipstream for us.
        pkg_zipstream = zipstream.ZipFile(mode='w',
                                          compression=zipstream.ZIP_DEFLATED)
        context['pkg_zipstream'] = pkg_zipstream

        toolkit.get_action('package_to_tabular_data_format')(context,
            {'id': package_id})

        return pkg_zipstream

    def resource_edit(self, id, resource_id, index=None, data=None,
                      errors=None, error_summary=None):

        if request.method == 'POST' and not data:

            # Get the form data that the user submitted.
            data = data or logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(
                        logic.parse_params(request.POST))))

            new_fields = {}
            for data_key, value in data.items():
                if not data_key.startswith('schema-'):
                    continue
                _, field_index, field_key = data_key.split('-', 2)
                if field_index in new_fields:
                    assert field_key not in new_fields[field_index]
                    new_fields[field_index][field_key] = value
                else:
                    new_fields[field_index] = {field_key: value}
            new_fields = new_fields.values()

            # The index of each field gets submitted as a string,
            # but in the db they're saved as ints. We need to convert them all
            # to ints so we can compare them.
            for field in new_fields:
                field['index'] = int(field['index'])

            current_fields = toolkit.get_action('resource_schema_show')(
                data_dict={'resource_id': resource_id}).get('fields', [])

            def get_field(index):
                '''
                Return the field with the given index from current_fields.
                '''
                matching_fields = [field for field in current_fields
                                   if field.get('index') == index]
                assert len(matching_fields) == 1, len(matching_fields)
                return matching_fields[0]

            fields_to_ignore = []
            fields_to_update = []
            fields_to_create = []
            fields_to_delete = []
            for field in new_fields:
                data_dict = {'resource_id': resource_id,
                             'index': field['index']}
                current_field = get_field(field['index'])
                if current_field != field:
                    fields_to_update.append(field)
                else:
                    fields_to_ignore.append(field)

                # TODO: Deal with fields to create. Catch exception above.

            for current_field in current_fields:
                if not [new_field for new_field in new_fields
                        if new_field['index'] == current_field['index']]:
                    fields_to_delete.append(current_field)

            # A sanity check.
            assert (len(fields_to_create) + len(fields_to_update) +
                    len(fields_to_delete) + len(fields_to_ignore)
                    == len(current_fields))

            def intersection(a, b):
                '''Return the intersection between two lists a and b.'''
                return [item for item in a if item in b]

            # More sanity checks.
            assert not intersection(fields_to_create, fields_to_update)
            assert not intersection(fields_to_create, fields_to_delete)
            assert not intersection(fields_to_update, fields_to_delete)
            assert not intersection(fields_to_ignore, fields_to_create)
            assert not intersection(fields_to_ignore, fields_to_update)
            assert not intersection(fields_to_ignore, fields_to_delete)

            data_dict = {'resource_id': resource_id}
            for field in fields_to_update:
                data_dict.update(field)
                toolkit.get_action('resource_schema_field_update')(
                        data_dict=data_dict)
            for field in fields_to_create:
                data_dict.update(field)
                toolkit.get_action('resource_schema_field_create')(
                        data_dict=data_dict)
            for field in fields_to_delete:
                data_dict['index'] = field['index']
                toolkit.get_action('resource_schema_field_update')(
                        data_dict=data_dict)

            current_resource = toolkit.get_action('resource_show')(
                data_dict={'id': data['id']})
            data['schema'] = current_resource['schema']

            # We don't want to include save "as it is part of the form" (?)
            del data['save']

            data['package_id'] = id

            context = {'model': model, 'session': model.Session,
                       'api_version': 3, 'for_edit': True,
                       'user': pylons.c.user or pylons.c.author,
                       'auth_user_obj': pylons.c.userobj}

            try:
                if resource_id:
                    data['id'] = resource_id
                    toolkit.get_action('resource_update')(context, data)
                else:
                    toolkit.get_action('resource_create')(context, data)
            except toolkit.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)
            except toolkit.NotAuthorized:
                toolkit.abort(401,
                              toolkit._('Unauthorized to edit this resource'))
            base.redirect(helpers.url_for(controller='package',
                                          action='resource_read',
                                          id=id,
                                          resource_id=resource_id))
        else:
            import ckan.controllers.package
            return ckan.controllers.package.PackageController().resource_edit(
                id, resource_id, data, errors, error_summary)
