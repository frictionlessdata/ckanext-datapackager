import ckan.plugins as plugins

class MixinPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IRoutes, inherit=True)

    def before_map(self, map_):
        map_.connect(
            'datapackager_import',
            '/import_datapackage',
            controller='ckanext.datapackager.controllers.datapackage:DataPackageController',
            action='import',
            conditions=dict(method=['GET', 'POST']),
        )
        map_.connect(
            'datapackager_export',
            '/dataset/{package_id}/datapackage.json',
            controller='ckanext.datapackager.controllers.datapackage:DataPackageController',
            action='export_datapackage'
        )
        return map_
