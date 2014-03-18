import os
import mock
import unittest

import pylons.config as config
import webtest
import ckanapi

import ckan
import ckan.model as model
import ckan.plugins
import ckan.plugins.toolkit as toolkit
import ckan.new_tests.helpers as helpers
import ckanext.datapackager.plugin as datapackager_plugin


class TestSimpleCsvPreviewPlugin(unittest.TestCase):
    @classmethod
    def setupClass(cls):
        cls.original_config = config.copy()
        plugins = set(config['ckan.plugins'].strip().split())
        plugins.add('simplecsvpreview')
        config['ckan.plugins'] = ' '.join(plugins)

        app = ckan.config.middleware.make_app(config['global_conf'], **config)
        cls.app = webtest.TestApp(app)

        cls.p = datapackager_plugin.SimpleCsvPreviewPlugin()

    @classmethod
    def tearDownClass(cls):
        config.clear()
        config.update(cls.original_config)

    def tearDown(self):
        helpers.reset_db()

    def test_can_preview(self):
        data_dict = {
            'resource': {
                'format': 'csv',
                'on_same_domain': True,
            }
        }
        self.assertEquals(True, self.p.can_preview(data_dict)['can_preview'])

    def test_not_same_domain(self):
        data_dict = {
            'resource': {
                'format': 'csv',
            }
        }
        self.assertEquals(False, self.p.can_preview(data_dict)['can_preview'])

    @mock.patch.object(ckan.lib.uploader.ResourceUpload, 'get_path')
    @mock.patch('ckan.plugins.toolkit.c')
    def test_csv_preview_data(self, c, mock_upload):
        #mock out all the resource upload stuff, we just want to check
        #the variable in c that setup_template_variables adds without
        #having to grep through all the messy html
        file_path = os.path.join(os.path.dirname(__file__),
                                 'test-data', 'data.csv')
        mock_upload.return_value = file_path
        data_dict = {
            'resource': {
                'id': 0,
                'format': 'csv',
                'on_same_domain': True,
            }
        }
        self.p.setup_template_variables({}, data_dict)

        #check that the csv data has been transposed
        expected_output = [
            ('date', '1950-01-01', '1950-02-01', '1950-03-01', '1950-04-01',
             '1950-05-01', '1950-06-01', '1950-07-01', '1950-08-01',
             '1950-09-01'),
            ('price', '34.730', '34.730', '34.730', '34.730', '34.730',
             '34.730', '34.730', '34.730', '34.730')
            ]
        self.assertEquals(expected_output, c.csv_preview_data)

    @mock.patch.object(ckan.lib.uploader.ResourceUpload, 'get_path')
    @mock.patch('ckan.plugins.toolkit.c')
    def test_csv_fewer_rows_than_preview_limit(self, c, mock_upload):
        '''test the behaviour when a csv file has fewer than the preview limit

        This test is for a fix for an unhandled stop iteraton exception
        '''
        #mock out all the resource upload stuff, we just want to check
        #the variable in c that setup_template_variables adds without
        #having to grep through all the messy html
        file_path = os.path.join(os.path.dirname(__file__),
                                 'test-data', 'small.csv')
        mock_upload.return_value = file_path
        data_dict = {
            'resource': {
                'id': 0,
                'format': 'csv',
                'on_same_domain': True,
            }
        }
        self.p.setup_template_variables({}, data_dict)

        #check that the csv data has been transposed
        expected_output = [
            ('date', '1950-01-01', '1950-02-01'),
            ('price', '34.730', '34.730')
        ]
        self.assertEquals(expected_output, c.csv_preview_data)

    @mock.patch.object(ckan.lib.uploader.ResourceUpload, 'get_path')
    @mock.patch('ckan.plugins.toolkit.c')
    def test_tab_seperated_file(self, c, mock_upload):
        '''test the behaviour when a previewing a tsb file '''
        file_path = os.path.join(os.path.dirname(__file__),
                                 'test-data', 'tab.csv')
        mock_upload.return_value = file_path
        data_dict = {
            'resource': {
                'id': 0,
                'format': 'csv',
                'on_same_domain': True,
            }
        }
        self.p.setup_template_variables({}, data_dict)

        #check that the csv data has been transposed
        expected_output = [
            ('date', '1950-01-01', '1950-02-01'),
            ('price', '34.730', '34.730')
        ]
        self.assertEquals(expected_output, c.csv_preview_data)

    @mock.patch.object(ckan.lib.uploader.ResourceUpload, 'get_path')
    @mock.patch('ckan.plugins.toolkit.c')
    def test_bad_csv_file(self, c, mock_upload):
        '''test with a csv file that generates a csv.Error when trying
        to sniff the 'dialect' of the csv file'''
        file_path = os.path.join(os.path.dirname(__file__),
                                 'test-data', 'bad.csv')
        mock_upload.return_value = file_path
        data_dict = {
            'resource': {
                'id': 0,
                'format': 'csv',
                'on_same_domain': True,
            }
        }
        self.p.setup_template_variables({}, data_dict)
        self.assertTrue(c.csv_error)

    @mock.patch('ckan.lib.datapreview._on_same_domain')
    def test_preview_template(self, same_domain):
        # patch so the file upload thinks it is on the same domain
        same_domain.return_value = True

        #create a test package and upload a test csv file
        usr = toolkit.get_action('get_site_user')({'model':model,'ignore_auth': True},{})
        package = helpers.call_action('package_create', name='test')
        api = ckanapi.TestAppCKAN(self.app, apikey=usr['apikey'])
        api.action.resource_create(
            package_id=package['id'],
            upload=open( os.path.join(os.path.dirname(__file__), 'test-data', 'data.csv')),
            format='csv',
            can_be_previewed=True,
        )
        #regrab the package for the id and resource id
        package = api.action.package_show(id=package['id'])

        #check the preview contains contains a table and check that some of the
        #values show up in the table
        resp = self.app.get('/dataset/{0}/resource/{1}/preview'.format(
            package['name'],  package['resources'][0]['id']))
        self.assertEquals('200 OK', resp.status)
        self.assertIn('<th>date</th>', resp.body)
        self.assertIn('<td>1950-01-01</td>', resp.body)
        self.assertIn('<th>price</th>', resp.body)
        self.assertIn('<td>34.730</td>', resp.body)
