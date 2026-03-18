from flask import Blueprint

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.datapackager.controllers import datapackage
from ckanext.datapackager.logic.action.create import package_create_from_datapackage
from ckanext.datapackager.logic.action.get import package_show_as_datapackage


class DataPackagerPlugin(plugins.SingletonPlugin):
    '''Plugin that adds importing/exporting datasets as Data Packages.
    '''
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    def update_config(self, config):
        toolkit.add_template_directory(config, '../templates')

    def get_actions(self):
        return {
            'package_create_from_datapackage': package_create_from_datapackage,
            'package_show_as_datapackage': package_show_as_datapackage,
        }

    def get_blueprint(self):
        blueprint = Blueprint("datapackager", __name__)
        # As long as the URL for import_datapackage_view and import_datapackage are the same, reverse lookups from import_datapackage will work
        blueprint.add_url_rule(
            "/import_datapackage",
            view_func=datapackage.new,
            endpoint="import_datapackage",
            methods=["GET"],
        )
        blueprint.add_url_rule(
            "/import_datapackage",
            view_func=datapackage.import_datapackage,
            endpoint="import_datapackage_post",
            methods=["POST"],
        )
        blueprint.add_url_rule(
            "/dataset/<package_id>/datapackage.json",
            view_func=datapackage.export_datapackage,
            endpoint="export_datapackage",
            methods=["GET"],
        )
        return blueprint
