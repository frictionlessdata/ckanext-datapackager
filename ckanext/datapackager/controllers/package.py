import zipstream

import pylons

from ckan.common import request
import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.base as base


def _extract_fields_from_data(data):
    '''Return the submitted form data in JSON Table Schema fields format.

    Takes data submitted by ckanext-datapackager's custom resource edit form
    and returns the same data as a list of dictionaries suitable for passing
    to resource_schema_field_create/delete.

    Expected input format:

        {'schema-0-index': '0',
         'schema-0-name': 'playerID',
         'schema-0-type': 'string',
         ...,
         'schema-1-index': '1',
         'schema-1-name': 'yearID',
         'schema-1-type': 'string',
         ...}

    Return format:

        [{'index': 0,
          'name': 'playerID',
          'type': 'string',
          ...},
         {'index': 1,
          'name': 'yearID',
          'type': 'string',
          ...},
        ...]

    Note that the 'index' values have been converted from strings to ints.

    In the list of dicts returned, the dicts are sorted by their 'index'
    values (even though they may not be sorted like this in the input data).

    Any "schema-*-*" keys will be returned, any other keys in the given data
    will be filtered out.

    '''
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

    # It's important for template rendering that the fields are sorted by
    # index.
    new_fields.sort(key=lambda x: x['index'])

    return new_fields

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

    def new_resource(self, package_id, data):
        import ckan.controllers.package
        return ckan.controllers.package.PackageController().new_resource(
            package_id, data)

    def _render_resource_edit_page_first_time(self, package_id, resource_id,
                                              data=None, errors=None,
                                              error_summary=None):
        '''Render the resource edit page for the first time.

        This happens when a user gets to the resource edit page for the first
        time (e.g. by clicking a link on another page) as opposed to already
        being on the resource edit page and clicking something on the page that
        causes it to reload. The data for the resource edit form needs to be
        retrieved from the database before rendering it.

        '''
        # Get the package dict and resource dict.
        context = {'api_version': 3, 'for_edit': True,
                   'user': toolkit.c.user or toolkit.c.author,
                   'auth_user_obj': toolkit.c.userobj}
        pkg_dict = toolkit.get_action('package_show')(context,
                                                      {'id': package_id})
        if pkg_dict['state'].startswith('draft'):
            resource_dict = toolkit.get_action('resource_show')(
                context, {'id': resource_id})
            fields = ['url', 'resource_type', 'format', 'name', 'description',
                      'id']
            data = {}
            for field in fields:
                data[field] = resource_dict[field]
            return self.new_resource(package_id, data=data)
        else:
            try:
                resource_dict = toolkit.get_action('resource_show')(
                    context, {'id': resource_id})
            except toolkit.ObjectNotFound:
                toolkit.abort(404, toolkit._('Resource not found'))

        # Setup template context variables.
        toolkit.c.pkg_dict = pkg_dict
        toolkit.c.resource = resource_dict
        toolkit.c.form_action = helpers.url_for(controller='package',
                                                action='resource_edit',
                                                resource_id=resource_id,
                                                id=package_id)

        # Setup template extra_vars.
        extra_vars = {
            'action': 'new',
            'selected_column': 0,
            'data': data or resource_dict,
            'errors': errors or {},
            'error_summary': error_summary or {},
            'schema_fields': toolkit.get_action('resource_schema_show')(
                data_dict={'resource_id': resource_id})['fields'],
        }

        return toolkit.render('package/resource_edit.html',
                              extra_vars=extra_vars)

    def _re_render_resource_edit_page(self, package_id, resource_id, data=None,
                                      errors=None, error_summary=None):
        '''Re-render the resource edit page, sending back the form data that
        the user submitted.

        This happens when the user clicks a button on the resource edit page
        that causes the page to be reloaded (e.g. clicking on one of the
        columns in the CSV preview). The page is re-rendered with any form
        values that the user had entered intact.

        '''
        # Find the "go-to-column-*" key. This key is set when the user clicks
        # on one of the columns in the CSV preview, it tells us which column
        # the user clicked on so we know which column to render as selected.
        matches = [key for key in request.params.keys()
                   if key.startswith("go-to-column-")]
        assert len(matches) == 1
        match = matches[0]
        selected_column = int(request.params[match])

        # Get the form data that the user submitted.
        data = data or logic.clean_dict(
            dict_fns.unflatten(
                logic.tuplize_dict(
                    logic.parse_params(request.POST))))

        schema_fields = _extract_fields_from_data(data)

        # Delete 'schema-*' and 'go-to-column-*' keys from the data.
        # These are part of the form/controller logic, not part of the user
        # data.
        for key in data.keys():
            if key.startswith('schema-'):
                del data[key]
            elif key.startswith('go-to-column-'):
                del data[key]

        # Setup template context variables.
        context = {'api_version': 3, 'for_edit': True,
                   'user': toolkit.c.user or toolkit.c.author,
                   'auth_user_obj': toolkit.c.userobj}
        toolkit.c.pkg_dict = toolkit.get_action('package_show')(
            context, {'id': package_id})
        resource_dict = toolkit.get_action('resource_show')(
            context, {'id': resource_id})
        toolkit.c.resource = resource_dict
        # set the form action
        toolkit.c.form_action = helpers.url_for(controller='package',
                                                action='resource_edit',
                                                resource_id=resource_id,
                                                id=package_id)

        # Setup template extra_vars.
        extra_vars = {
            'schema_fields': schema_fields,
            'selected_column': selected_column,
            'data': data or resource_dict,
            'errors': errors or {},
            'error_summary': error_summary or {},
            'action': 'new',
        }

        return toolkit.render('package/resource_edit.html',
                              extra_vars=extra_vars)

    def _update_resource(self, package_id, resource_id, data):
        '''Update a resource and redirect to the resource_read page.

        This happens when the user clicks the Save button on the resource_edit
        page. The form values they submit are saved to the database and they're
        sent to the resource_read page.

        '''
        # Get the form data that the user submitted.
        data = data or logic.clean_dict(
            dict_fns.unflatten(
                logic.tuplize_dict(
                    logic.parse_params(request.POST))))

        # Delete 'save' from the data because it's part of the form/controller
        # logic not part of the user data.
        del data['save']

        new_fields = _extract_fields_from_data(data)

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

        # Compae new_fields and current_fields to figure out which resource
        # schema fields need to be created, updated and deleted.
        fields_to_ignore = []
        fields_to_update = []
        fields_to_create = []
        fields_to_delete = []
        for field in new_fields:
            data_dict = {'resource_id': resource_id, 'index': field['index']}
            current_field = get_field(field['index'])
            if current_field != field:
                fields_to_update.append(field)
            else:
                fields_to_ignore.append(field)

            # TODO: Deal with fields to create. Catch exception above.

        # Find the fields that need to be deleted.
        for current_field in current_fields:
            if not [new_field for new_field in new_fields
                    if new_field['index'] == current_field['index']]:
                fields_to_delete.append(current_field)

        # A sanity check.
        assert (len(fields_to_create) + len(fields_to_update) +
                len(fields_to_delete) + len(fields_to_ignore)
                == len(current_fields))

        # Create, update and delete the resource schema fields as necessary.
        # TODO: Deal with exceptions here.
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

        # Add the current resource schema into the data dict, so that
        # resource_update doesn't delete it.
        current_resource = toolkit.get_action('resource_show')(
            data_dict={'id': data['id']})
        data['schema'] = current_resource['schema']

        # Update the resource itself (e.g. if the user has changed the
        # resource's name or file).
        data['package_id'] = package_id
        data['id'] = resource_id
        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True,
                   'user': pylons.c.user or pylons.c.author,
                   'auth_user_obj': pylons.c.userobj}
        try:
            toolkit.get_action('resource_update')(context, data)
        except toolkit.ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.resource_edit(package_id, resource_id, data,
                                      errors, error_summary)
        except toolkit.NotAuthorized:
            toolkit.abort(401,
                          toolkit._('Unauthorized to edit this resource'))

        # Finally, redirect the user to the resource_read page.
        base.redirect(helpers.url_for(controller='package',
                                      action='resource_read',
                                      id=package_id,
                                      resource_id=resource_id))

    def resource_edit(self, id, resource_id, index=None, data=None,
                      errors=None, error_summary=None):

        if request.method == 'GET':
            return self._render_resource_edit_page_first_time(
                id, resource_id, data, errors, error_summary)

        elif request.method == 'POST' and 'save' in request.params:
            return self._update_resource(id, resource_id, data)

        else:
            return self._re_render_resource_edit_page(id, resource_id, data,
                                                      errors, error_summary)
