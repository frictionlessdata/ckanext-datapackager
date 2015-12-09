import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.logic.action.create
import ckanext.datapackager.logic.action.get


class DownloadTabularDataFormatPlugin(plugins.SingletonPlugin):
    '''Plugin that adds downloading packages in Tabular Data Format.

    Adds a Download button to package pages that downloads a Tabular Data Format
    ZIP file of the package. Also adds an API for getting a package descriptor
    Simple Data Format JSON.

    '''
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates/download_tdf')

    def before_map(self, map_):
        map_.connect('/package/{package_id}/download_tabular_data_format',
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format')
        return map_

    def get_actions(self):
        return {
            'package_create_from_datapackage':
                ckanext.datapackager.logic.action.create.package_create_from_datapackage,
            'package_to_tabular_data_format':
                ckanext.datapackager.logic.action.get.package_to_tabular_data_format,
            'package_to_tabular_data_format_zip':
                ckanext.datapackager.logic.action.get.package_to_tabular_data_format_zip,
        }
