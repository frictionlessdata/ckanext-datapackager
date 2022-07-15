import ckan.plugins as plugins

<<<<<<<< HEAD:ckanext/datapackager/plugin/pylons_plugin.py
class MixinPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)
    
========

class DataPackagerPlugin(plugins.SingletonPlugin):
    '''Plugin that adds importing/exporting datasets as Data Packages.
    '''
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    #plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

>>>>>>>> 5d0de0697d000efcab4888edda8751845e49f2d2:ckanext/datapackager/plugin/__init__.py
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