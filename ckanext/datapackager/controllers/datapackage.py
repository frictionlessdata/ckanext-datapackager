import json

import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckanext.datapackager import utils


class DataPackageController(toolkit.BaseController):
    def new(self, data=None, errors=None, error_summary=None):
        return utils.new(data, errors, error_summary)

    def import_datapackage(self):
        return utils.import_datapackage()

    def export_datapackage(self, package_id):
        '''Return the given dataset as a Data Package JSON file.

        '''
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
        }
        r = toolkit.response
        r.content_disposition = 'attachment; filename=datapackage.json'.format(
            package_id)
        r.content_type = 'application/json'

        try:
            datapackage_dict = toolkit.get_action(
                'package_show_as_datapackage')(
                context,
                {'id': package_id}
            )
        except toolkit.ObjectNotFound:
            toolkit.abort(404, 'Dataset not found')

        return json.dumps(datapackage_dict, indent=2)
