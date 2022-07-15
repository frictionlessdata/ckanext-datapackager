import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.logic.action.create
import ckanext.datapackager.logic.action.get


class DataPackagerPluginBase(plugins.SingletonPlugin):
    pass


if toolkit.check_ckan_version(u'2.9'):
    from ckanext.datapackager.plugin.flask_plugin import MixinPlugin
    ckan_29_or_higher = True
else:
    from ckanext.datapackager.plugin.pylons_plugin import MixinPlugin
    ckan_29_or_higher = False

class DataPackagerPlugin(DataPackagerPluginBase, MixinPlugin):
    '''Plugin that adds importing/exporting datasets as Data Packages.
    '''
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)

    def update_config(self, config):
        toolkit.add_template_directory(config, '../templates')

    def get_actions(self):
        return {
            'package_create_from_datapackage':
                ckanext.datapackager.logic.action.create.package_create_from_datapackage,
            'package_show_as_datapackage':
                ckanext.datapackager.logic.action.get.package_show_as_datapackage,
        }

    def before_map(self, map_):
        map_.connect(
            'import_datapackage',
            '/import_datapackage',
            controller='ckanext.datapackager.controllers.datapackage:DataPackageController',
            action='new',
            conditions=dict(method=['GET']),
        )
        map_.connect(
            'import_datapackage',
            '/import_datapackage',
            controller='ckanext.datapackager.controllers.datapackage:DataPackageController',
            action='import_datapackage',
            conditions=dict(method=['POST']),
        )
        map_.connect(
            'export_datapackage',
            '/dataset/{package_id}/datapackage.json',
            controller='ckanext.datapackager.controllers.datapackage:DataPackageController',
            action='export_datapackage'
        )
        return map_
