import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.logic.action.create
import ckanext.datapackager.logic.action.get


class DownloadTabularDataFormatPlugin(plugins.SingletonPlugin):
    '''Plugin that adds downloading packages in Tabular Data Format.

    Adds a API endpoint and download button to package pages that downloads a
    Tabular Data Format JSON file of the package.

    '''
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')

    def before_map(self, map_):
        map_.connect(
            'import_data_package',
            '/import_data_package',
            controller='ckanext.datapackager.controllers.data_package:DataPackageController',
            action='new',
            conditions=dict(method=['GET']),
        )
        map_.connect(
            'import_data_package',
            '/import_data_package',
            controller='ckanext.datapackager.controllers.data_package:DataPackageController',
            action='import_data_package',
            conditions=dict(method=['POST']),
        )
        map_.connect(
            'download_tabular_data_format',
            '/dataset/{package_id}/download_tabular_data_format',
            controller='ckanext.datapackager.controllers.data_package:DataPackageController',
            action='download_tabular_data_format'
        )
        return map_

    def get_actions(self):
        return {
            'package_create_from_datapackage':
                ckanext.datapackager.logic.action.create.package_create_from_datapackage,
            'package_to_tabular_data_format':
                ckanext.datapackager.logic.action.get.package_to_tabular_data_format,
        }
