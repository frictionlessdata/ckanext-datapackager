import ckan.plugins as plugins

from flask import Blueprint
from ckanext.datapackager.blueprint import blueprint

class MixinPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IBlueprint)

    def get_blueprint(self):
      return blueprint
