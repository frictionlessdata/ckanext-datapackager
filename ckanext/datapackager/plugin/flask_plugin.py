import ckan.plugins as plugins

from flask import Blueprint
import ckanext.datapackager.controllers.datapackage as datapackage

class MixinPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IBlueprint)
    
    def get_blueprint(self):
        blueprint = Blueprint('datapackager', __name__)
        # As long as the URL for import_datapackage_view and import_datapackage are the same, reverse lookups from import_datapackage will work
        blueprint.add_url_rule("/import_datapackage", view_func=datapackage.new, endpoint='import_datapackage', methods=['GET'])
        blueprint.add_url_rule("/import_datapackage", view_func=datapackage.import_datapackage, endpoint='import_datapackage_post', methods=['POST'])
        blueprint.add_url_rule("/dataset/<package_id>/datapackage.json", view_func=datapackage.export_datapackage, endpoint='export_datapackage', methods=['GET'])
        return blueprint