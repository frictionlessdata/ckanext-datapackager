import ckan.plugins as plugins

class MixinPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)

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
