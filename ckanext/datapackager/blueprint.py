from flask import Blueprint, make_response
import json

import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckanext.datapackager import utils


blueprint = Blueprint('datapackager', __name__)


def export_datapackage(package_id):
    '''Return the given dataset as a Data Package JSON file.

    '''
    context = {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
    }
    try:
        datapackage_dict = toolkit.get_action(
            'package_show_as_datapackage')(
            context,
            {'id': package_id}
        )
    except toolkit.ObjectNotFound:
        toolkit.abort(404, 'Dataset not found')

    r = make_response(json.dumps(datapackage_dict, indent=2))
    r.headers['Content-disposition'] = 'attachment; filename=datapackage.json'.format(
        package_id)
    r.headers['Content-type'] = 'application/json'

    return r

# As long as the URL for import_datapackage_view and import_datapackage are the same, reverse lookups from import_datapackage will work
blueprint.add_url_rule("/import_datapackage", view_func=utils.new, endpoint='import_datapackage', methods=['GET'])
blueprint.add_url_rule("/import_datapackage", view_func=utils.import_datapackage, endpoint='import_datapackage_post', methods=['POST'])
blueprint.add_url_rule("/dataset/<package_id>/datapackage.json", view_func=export_datapackage, endpoint='export_datapackage', methods=['GET'])
