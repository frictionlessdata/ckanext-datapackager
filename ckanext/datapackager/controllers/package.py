import zipstream

import pylons

from ckan.common import request
import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.base as base


def _get_data():
    '''Return the data posted by the resource edit form.'''

    return dict(request.params)


def _extract_fields_from_data(data):
    '''Transform data submitted by the resource edit form into
    JSON Table Schema fields format.

    Takes data submitted by ckanext-datapackager's custom resource edit form
    and returns the same data as a list of dictionaries suitable for passing
    to resource_schema_field_create() or _update().

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

    # Convert '__new_attr_key' and '__new_attr_value' into a single
    # '__new_attr' dictionary with 'key' and 'value' keys.
    for field in new_fields:
        field['__new_attr'] = {
            'key': field['__new_attr_key'],
            'value': field['__new_attr_value']
        }
        del field['__new_attr_key']
        del field['__new_attr_value']

    return new_fields


def _group_submitted_fields(new_fields, resource_id):
    '''Return the resource schema fields that need to be created, updated or
    deleted.

    Compares the given fields to those in the db and returns three lists:
    the fields that need to be created, those that need to be updated and those
    that need to be deleted from the db.

    Fields that are the same as those already in the db, are not in any of the
    three lists returned.

    :param new_fields: the new schema fields submitted by the resource edit
        form
    :type new_fields: list of dictionaries

    :returns: a tuple of three lists: the fields that need to be created,
        those that need to be updated, and those that need to be deleted from
        the db
    :rtype: tuple

    '''
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

    # Compare new_fields and current_fields to figure out which resource
    # schema fields need to be created, updated and deleted.
    fields_to_ignore = []
    fields_to_create = []
    fields_to_update = []
    fields_to_delete = []
    for field in new_fields:
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

    return fields_to_create, fields_to_update, fields_to_delete


def _call_actions(schema_fields, resource_id, validate_only=False):
    '''Call the resource_schema_field_create(), _update() and _delete()
    action functions to create, update and delete the given resource
    schema fields.

    Compare the given resource fields to the fields currently in the database
    and figure out which of the given fields are unchanged, changed or new,
    and which of the fields in the db are missing from the given fields, then
    call the _create(), _update() and _delete() APIs as necessary to update any
    new, changed or deleted fields.

    For fields where the given field is the same as what's already in the
    database, no action function will be called.

    :param schema_fields: the new schema fields submitted by the resource
        edit form
    :type schema_fields: list of dicts

    :param resource_id: the ID of the resource being edited
    :type resource_id: string

    :param validate_only: this will be passed to the action functions, if True
        it causes them to validate the given data only and not actually update
        the database (optional, default: False)

    :returns: a list of dicts containing the validation errors that the
        actions gave for each field (or empty dicts, where the action was
        successful).
    :rtype: list of dicts

    '''
    # Copy schema_fields because we don't want to edit it.
    # (Note we deliberately copy each of the dicts in schema_fields.)
    schema_fields = [field.copy() for field in schema_fields]

    # Delete '__new_attr' items, we don't want to save these in the db.
    for field in schema_fields:
        del field['__new_attr']

    fields_to_create, fields_to_update, fields_to_delete = (
        _group_submitted_fields(schema_fields, resource_id))

    schema_errors = [{} for field in schema_fields]

    data_dict = {'resource_id': resource_id}
    errors_found = False
    for field in fields_to_update:
        data_dict.update(field)
        try:
            toolkit.get_action('resource_schema_field_update')(
                data_dict=data_dict, validate_only=validate_only)
        except toolkit.ValidationError as exc:
            index = schema_fields.index(field)
            schema_errors[index] = exc.error_dict
            errors_found = True

    for field in fields_to_create:
        data_dict.update(field)
        toolkit.get_action('resource_schema_field_create')(
            data_dict=data_dict)

    for field in fields_to_delete:
        data_dict['index'] = field['index']
        toolkit.get_action('resource_schema_field_update')(
            data_dict=data_dict)

    # The validation exceptions contain lists of strings for each attribute
    # that has validation errors. Concatenate those lists into single strings.
    if errors_found:
        for field_error_dict in schema_errors:
            for key in field_error_dict:
                field_error_dict[key] = '\n'.join(
                    field_error_dict[key])

    return schema_errors


def _delete_form_logic_keys(data):
    '''Return a copy of the given data dict with certain keys filtered out.

    The data dict should be one submitted by the resource edit form.

    The filtered keys are part of the form/controller logic and not
    user-submitted data. They shouldn't be passed to action functions for
    saving in the db, for example.

    '''
    new_data = {}
    for key in data.keys():
        if not (key.startswith('schema-') or
            key.startswith('go-to-column-') or
            key in ('schema_errors', 'save', 'add-new-attr')):
            new_data[key] = data[key]
    return new_data


def _selected_column():
    '''Return the index number of the column that the user clicked on.

    When the user clicks on a column in the CSV preview on the resource
    edit form, the index number of the column is submitted with a
    "go-to-column-*" key as part of the form data.

    Find the value of that key in the form data, convert it to an int, and
    return it.

    Returns 0 if there's no go-to-column-* key, or if the key has an invalid
    value.

    '''
    matching_keys = [key for key in request.params.keys()
                     if key.startswith("go-to-column-")]
    assert len(matching_keys) in (0, 1), ("There should never be more than "
                                          "one 'go-to-column-*' key submitted")
    if matching_keys:
        matching_key = matching_keys[0]
        try:
            selected_column = int(request.params[matching_key])
        except ValueError:
            selected_column = 0
    else:
        selected_column = 0

    return selected_column


def _first_column_with_errors(schema_errors):
    '''Return the index of the first column in the given schema_errors list
    that has an error.

    Returns None if there are no columns with errors.

    '''
    for index, errors_dict in enumerate(schema_errors):
        if errors_dict:
            return index
    return None


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

        # Get the resource schema fields that will be passed to the template
        # for rendering into the form.
        schema_fields = toolkit.get_action('resource_schema_show')(
            data_dict={'resource_id': resource_id})['fields']

        # We add one __new_attr entry into each field, this is used when the
        # user wants to add a new attribute to a field.
        for field in schema_fields:
            assert '__new_attr' not in field, ("__new_attr keys are never "
                                               "saved in the db")
            field['__new_attr'] = {'key': '', 'value': ''}


        # Setup template extra_vars.
        schema_errors = [{} for field in schema_fields]
        extra_vars = {
            'action': 'new',
            'selected_column': 0,
            'data': data or resource_dict,
            'errors': errors or {},
            'error_summary': error_summary or {},
            'schema_fields': schema_fields,
            'schema_errors': schema_errors,
        }

        return toolkit.render('package/resource_edit.html',
                              extra_vars=extra_vars)

    def _re_render_resource_edit_page(self, package_id, resource_id, data=None,
                                      errors=None, error_summary=None,
                                      schema_errors=None):
        '''Re-render the resource edit page, sending back the form data that
        the user submitted.

        This happens when the user clicks a button on the resource edit page
        that causes the page to be reloaded (e.g. clicking on one of the
        columns in the CSV preview). The page is re-rendered with any form
        values that the user had entered intact.

        '''
        # Get the form data that the user submitted.
        data = data or _get_data()
        schema_fields = _extract_fields_from_data(data)
        # FIXME: This actually validates the data in all of the resource schema
        # fields, when we only really need to validate the field for the
        # currently selected column.
        schema_errors = schema_errors or _call_actions(schema_fields,
                                                       resource_id,
                                                       validate_only=True)

        # Setup template context variables.
        toolkit.c.pkg_dict = toolkit.get_action('package_show')(
                {'for_edit': True}, {'id': package_id})
        toolkit.c.resource = toolkit.get_action('resource_show')(
                {'for_edit': True}, {'id': resource_id})
        toolkit.c.form_action = helpers.url_for(controller='package',
                                                action='resource_edit',
                                                resource_id=resource_id,
                                                id=package_id)

        # We show the first column whose schema fields have any validation
        # errors, or if no columns have validation errors then we show the
        # column that the user clicked on.
        selected_column = _first_column_with_errors(schema_errors)
        if selected_column is None:
            selected_column = _selected_column()

        # Setup template extra_vars.
        extra_vars = {
            'schema_fields': schema_fields,
            'schema_errors': schema_errors,
            'selected_column': selected_column,
            'data': _delete_form_logic_keys(data) or toolkit.c.resource,
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

        If there are any validation errors when trying to save the submitted
        values, then the edit form is re-rendered with the error messages
        instead of redirectin to the read page.

        '''
        # Get the form data that the user submitted.
        data = data or _get_data()
        new_fields = _extract_fields_from_data(data)

        data = _delete_form_logic_keys(data)

        # Try to create, update and delete all the resource schema fields in
        # db as necessary.
        schema_errors = _call_actions(new_fields, resource_id)

        # If there were errors, re-render the resoure edit form with the error
        # messages.
        for error_dict in schema_errors:
            if error_dict:
                # Setup the template context and extra_vars that the form needs
                # and render the form.
                toolkit.c.pkg_dict = toolkit.get_action('package_show')(
                    {'for_edit': True}, {'id': package_id})
                toolkit.c.resource = toolkit.get_action('resource_show')(
                    {'for_edit': True}, {'id': resource_id})
                toolkit.c.form_action = helpers.url_for(
                    controller='package', action='resource_edit',
                    resource_id=resource_id, id=package_id)
                extra_vars = {
                    'schema_fields': new_fields,
                    'schema_errors': schema_errors,
                    'selected_column':
                        _first_column_with_errors(schema_errors),
                    'data': data or toolkit.c.resource,
                    'errors': {},
                    'error_summary': {},
                    'action': 'new',
                }
                return toolkit.render('package/resource_edit.html',
                                      extra_vars=extra_vars)


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

    def _add_attr_to_schema_field(self, package_id, resource_id):
        '''Add a new attribute to the selected schema field and re-render the
        form.

        This is called when the user submits the resource edit form by clicking
        the plus button in the 'Add a new attribute' section. The values
        entered into the key and value inputs are converted into a new
        top-level item in the schema field dict, and the
        'Add a new attribute' section is cleared ready to add another
        attribute.

        Note that this doesn't actually save the new attribute in the db,
        that doesn't happen until the user clicks the Save button.

        '''
        data = _get_data()
        schema_fields = _extract_fields_from_data(data)

        # Find the column index and field dict that we are trying to add a new
        # attribute to.
        selected_column = int(request.params['add-new-attr'])
        selected_field = schema_fields[selected_column]

        # Add the new attribute.
        new_key = selected_field['__new_attr']['key'].strip()
        new_value = selected_field['__new_attr']['value'].strip()
        if new_key:
            # FIXME: This will overwrite an existing field with the same key.
            # Instead of overwriting we should show the user an error.
            selected_field[new_key] = new_value

            # Clear the 'Add a new attribute' <input>s, ready to add another
            # new attribute.
            selected_field['__new_attr'] = {'key': '', 'value': ''}

        # The user may have edited the values of some existing field attributes
        # as well, so validate the field attributes and show any errors to the
        # user.
        # FIXME: This validates every resource schema field, but we only need
        # to validate the field for the currently selected column.
        schema_errors = _call_actions(schema_fields, resource_id,
                                      validate_only=True)

        # Setup template context variables.
        toolkit.c.pkg_dict = toolkit.get_action('package_show')(
            {'for_edit': True}, {'id': package_id})
        toolkit.c.resource = toolkit.get_action('resource_show')(
            {'for_edit': True}, {'id': resource_id})
        toolkit.c.form_action = helpers.url_for(controller='package',
                                                action='resource_edit',
                                                resource_id=resource_id,
                                                id=package_id)

        # Setup template extra_vars.
        extra_vars = {
            'schema_fields': schema_fields,
            'schema_errors': schema_errors,
            'selected_column': selected_column,
            'data': _delete_form_logic_keys(data),
            'errors': {},
            'error_summary': {},
            'action': 'new',
        }

        return toolkit.render('package/resource_edit.html',
                              extra_vars=extra_vars)

    def resource_edit(self, id, resource_id, index=None, data=None,
                      errors=None, error_summary=None):

        if request.method == 'GET':
            return self._render_resource_edit_page_first_time(
                id, resource_id, data, errors, error_summary)

        elif request.method == 'POST' and 'save' in request.params:
            return self._update_resource(id, resource_id, data)

        elif (request.method == 'POST' and 'add-new-attr' in request.params):
            return self._add_attr_to_schema_field(id, resource_id)
        else:
            return self._re_render_resource_edit_page(id, resource_id, data,
                                                      errors, error_summary)
