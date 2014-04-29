import zipstream

from ckan.common import request
import ckan.model as model
import ckan.lib.helpers as helpers
import ckan.plugins.toolkit as toolkit


def _regroup_fields(request_dict, deleted=None):
    '''Regroups the fields in a dictionary submitted

    The form from our editor will submit the dict like:

    {'name-fielda': 'fielda',
     'value-fielda:'some value',
     'name-fieldb': 'fieldb',
     'value-fieldb': 'some other value'}

    we want to regroup the fields to be:
    {'fielda': 'some value',
     'fieldb': 'some other value'}'''
    def _is_valid_key(key):
        if key.startswith('name-') and key != deleted:
            return True
        else:
            return False

    #only get the field names, not the values
    fields = [i for i in request_dict.keys() if _is_valid_key(i)]

    data_dict = {}
    for field in fields:
        #ignore empty keys and values, should fix this in the schema
        field_name = request_dict[field]
        if field_name == '':
            continue

        #strip out the name- from the field name
        i = field[len('name-'):]
        #get value-form field associated with this key
        value = request_dict['value-{0}'.format(i)]
        data_dict[request_dict[field]] = value

    return data_dict


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

    def _posted_metadata(self, context, resource_id, index, request_dict):
        #check if we pushed a delete button
        deleted = request_dict.get('delete')
        data_dict = _regroup_fields(request_dict, deleted)
        data_dict.update({'resource_id': resource_id, 'index': index})
        return toolkit.get_action('resource_schema_field_update')(context, data_dict)

    def edit_metadata_field(self, package_id, resource_id, index):
        context = {'model': model, 'session': model.Session}

        errors = None
        if request.method == 'POST':
            try:
                schema_form = self._posted_metadata(context, resource_id,
                                                    index, request.POST)
            except toolkit.ValidationError, e:
                errors = e.error_dict
                #recover the original values posted to the form otherwise we
                #end up deleting the user's input
                schema_form = _regroup_fields(request.POST)
            except toolkit.NotAuthorized:
                toolkit.abort(401, toolkit._('Unauthorized to edit this resource'))
        else:
            schema_form = toolkit.get_action('resource_schema_field_show')(
                context, {'resource_id': resource_id, 'index': index})

        #remove index, we don't want the user editing it.
        schema_form.pop('index', None)

        vars = {'errors': errors, 'schema_form': schema_form, 'column': index}
        return toolkit.render('package/schema_edit_form.html', extra_vars=vars)
