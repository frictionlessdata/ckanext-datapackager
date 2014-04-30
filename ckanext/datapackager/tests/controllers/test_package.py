'''Functional tests for controllers/package.py.'''
import os
import zipfile
import StringIO
import json

import nose.tools
import bs4
import ckanapi

from ckan.common import OrderedDict
import ckan.model as model
import ckan.new_tests.factories as factories
import ckan.new_tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.datapackager.tests.helpers as custom_helpers
import ckanext.datapackager.controllers.package as package_controller
import ckanapi


def _get_csv_file(relative_path):
        path = os.path.join(os.path.split(__file__)[0], relative_path)
        abspath = os.path.abspath(path)
        csv_file = open(abspath)
        return csv_file


class TestDataPackagerPackageController(
        custom_helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackagerPackageController class.'''

    def test_add_package(self):
        '''Test the custom two-step add package process.

        CKAN's three-step add dataset process should be changed into a two-step
        process, with the user being redirected to the package read page after
        the second step.

        '''
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}
        package_title = 'my test package'
        package_name = 'my-test-package'

        # Get the new package page (first form).
        response = self.app.get('/package/new', extra_environ=extra_environ)
        assert response.status_int == 200

        # Fill out the form and submit it.
        form = response.forms[0]
        form['title'] = package_title
        form['name'] = package_name
        form['version'] = '0.1beta'
        form['notes'] = 'Just a test package nothing to see here'
        response = form.submit('save', extra_environ=extra_environ)

        # Follow the redirect to the second form.
        assert response.status_int == 302
        response = response.follow(extra_environ=extra_environ)

        assert response.status_int == 200

        # Get the CSV file to upload.
        path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
        path = os.path.join(os.path.split(__file__)[0], path)
        abspath = os.path.abspath(path)

        # Fill out the form and submit it.
        form = response.forms[0]
        form['upload'] = ('upload', abspath)
        form['name'] = 'My test CSV file'
        response = form.submit('save', extra_environ=extra_environ)

        # Follow the redirect to the third form.
        assert response.status_int == 302
        assert '/dataset/new_metadata/my-test-package' in response.location, response.location
        response = response.follow(extra_environ=extra_environ)

        # The third form immediately redirects you to the dataset read page.
        assert response.status_int == 302
        assert '/package/my-test-package' in response.location
        response = response.follow(extra_environ=extra_environ)

        assert response.status_int == 200

        # Test that the package and resource were created.
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        package = api.action.package_show(id='my-test-package')
        assert package['title'] == 'my test package'
        assert package['state'] == 'active'
        resources = package['resources']
        assert len(resources) == 1

        # Test that the schema was inserted into the resource.
        # (Unit tests elsewhere test whether the contents of the schemas are
        # correct.)
        resource = resources[0]
        assert 'schema' in resource
        schema = resource['schema']
        assert 'fields' in schema

    def test_download_tdf(self):
        '''Test downloading a Tabular Data Format ZIP file of a package.

        '''
        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        # Add a resource with a linked-to, not uploaded, data file.
        linked_resource = factories.Resource(dataset=dataset,
            url='http://test.com/test-url-1',
            schema='{"fields":[{"type":"string", "name":"col1"}]}')

        # Add a resource with an uploaded data file.
        csv_path = '../test-data/lahmans-baseball-database/AllstarFull.csv'
        csv_file = _get_csv_file(csv_path)
        api.action.resource_create(package_id=dataset['id'],
            name='AllstarFull.csv', upload=csv_file)

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
                                 ['AllstarFull.csv', 'datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])

        resources = datapackage['resources']
        nose.tools.assert_equals(linked_resource['url'], resources[0]['url'])
        schema = resources[0]['schema']
        nose.tools.assert_equals(
            {'fields': [{'type': 'string', 'name': 'col1'}]}, schema)

        nose.tools.assert_equals(resources[1]['path'], 'AllstarFull.csv')

        # Check the contenst of the AllstarFull.csv file.
        assert (zip_.open('AllstarFull.csv').read() ==
                _get_csv_file(csv_path).read())

    def test_download_tdf_with_three_files(self):
        '''Upload three CSV files to a package and test downloading the ZIP.'''

        user = factories.Sysadmin()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        dataset = factories.Dataset()

        def filename(path):
            return os.path.split(path)[1]

        csv_paths = ('../test-data/lahmans-baseball-database/AllstarFull.csv',
            '../test-data/lahmans-baseball-database/PitchingPost.csv',
            '../test-data/lahmans-baseball-database/TeamsHalf.csv')
        for path in csv_paths:
            csv_file = _get_csv_file(path)
            api.action.resource_create(package_id=dataset['id'],
                name=filename(path), upload=csv_file)

        # Download the package's SDF ZIP file.
        url = toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])
        response = self.app.get(url)

        # Open the response as a ZIP file.
        zip_ = zipfile.ZipFile(StringIO.StringIO(response.body))

        # Check that the ZIP file contains the files we expect.
        nose.tools.assert_equals(zip_.namelist(),
            [filename(path) for path in csv_paths] + ['datapackage.json'])

        # Extract datapackage.json from the zip file and load it as json.
        datapackage = json.load(zip_.open('datapackage.json'))

        # Check the contents of the datapackage.json file.
        nose.tools.assert_equals(dataset['name'], datapackage['name'])
        resources = datapackage['resources']
        for csv_path, resource in zip(csv_paths, resources):
            nose.tools.assert_equals(resource['path'], filename(csv_path))
            assert 'schema' in resource

        # Check the contents of the CSV files.
        for csv_path in csv_paths:
            assert (zip_.open(filename(csv_path)).read() ==
                    _get_csv_file(csv_path).read())

    def test_that_download_button_is_on_page(self):
        '''Tests that the download button is shown on the package pages.'''

        dataset = factories.Dataset()

        response = self.app.get('/package/{0}'.format(dataset['name']))
        soup = response.html
        download_button = soup.find(id='download_tdf_button')
        download_url = download_button['href']
        assert download_url == toolkit.url_for(
            controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
            action='download_tabular_data_format',
            package_id=dataset['name'])

    def test_view_edit_metadata(self):
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}
        #create test package and resource
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'lahmans-baseball-database', 'AllstarFull.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        response = self.app.get('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            extra_environ=extra_environ)
        soup = bs4.BeautifulSoup(response.body)
        form_dict = dict((i.attrs['name'], i.attrs['value'])
            for i in soup.form.findAll('input'))

        nose.tools.assert_equals(sorted(form_dict.items()),
            sorted({
                u'name-type': u'type',
                u'value-type': u'string',
                u'name-name': u'name',
                u'value-2': u'',
                u'name-2': u'',
                u'value-name': u'playerID'
            }.items())
        )

    def test_submit_metadata(self):
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        #create test package and upload a test csv file.
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'data.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #post new data to the metadata editor
        #webtest multiple submit does not work so we cannot use the response.forms
        #form.submit('delete', index=0) does not work and is bugged in our current
        #version of web test!
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
                (u'name-2', u'new'),(u'value-2', u'new value'),
                (u'name-name', u'name'),  (u'value-name', u'date'),
            ]),
            extra_environ=extra_environ,
        )

        #check that our new metadata has been saved to the resource
        resource_schema_field = api.action.resource_schema_field_show(
            index=0, resource_id=resource['id'])

        #check that the output matches.
        expected_output = {
            u'index': 0,
            u'type': u'string',
            u'name': u'date',
            u'new': u'new value'
        }

        nose.tools.assert_equals(
            sorted(resource_schema_field),
            sorted(expected_output)
        )

    def test_delete_metadata(self):
        '''test that deletion from a schema field through the editor works'''
        user = factories.User()
        extra_environ = {
            'REMOTE_USER': str(user['name']),
        }

        #create test package and upload a test csv file.
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'data.csv')
        upload = open(path)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        package = api.action.package_create(name='test-package')
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #post new data to the metadata editor removing one of the elements
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
                (u'name-name', u'name'),  (u'value-name', u'date'),
                (u'delete', u'name-type'),
            ]),
            extra_environ=extra_environ,
        )

        #save me some future debugging time
        #we should not have a validation error here, we constructed the dict!
        assert not 'The following errors were found' in response.body

        #check that our new metadata has been saved to the resource
        resource_schema_field = api.action.resource_schema_field_show(
            index=0, resource_id=resource['id'])

        #check that the output matches.
        expected_output = {
            u'index': 0,
            u'name': u'date',
        }

        nose.tools.assert_equals(
            sorted(resource_schema_field.items()),
            sorted(expected_output.items())
        )

    def test_editor_raises_validation_error(self):
        '''test that a validation error is raised when no name is given and
        is a required field '''
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        #create test package and upload a test csv file.
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'data.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #post new data to the metadata editor removing one of the elements
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
            ]),
            extra_environ=extra_environ,
        )
 
        #check that an error message has been displayed
        nose.tools.assert_in(
            'The following errors were found',
            response.body
        )

    def test_editor_with_unauthorized_user(self):
        user = factories.User()
        #create test package and resource
        path = os.path.join(os.path.dirname(__file__), os.pardir, 'test-data',
                            'lahmans-baseball-database', 'AllstarFull.csv')
        upload = open(path)
        package = helpers.call_action('package_create', name='test-package')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(
            package_id=package['id'],
            upload=upload,
            format='csv',
            can_be_previewed=True,
        )

        #make an unauthorized request to the editor.
        response = self.app.post('/package/{0}/file/{1}/schema/0/edit'.format(package['id'], resource['id']),
            OrderedDict([
                (u'name-type', u'type'), (u'value-type', u'string'),
                (u'name-2', u'new'),(u'value-2', u'new value'),
                (u'name-name', u'name'),  (u'value-name', u'date'),
            ]),
        )
        #test that we were redirected to the login page
        nose.tools.assert_equals(302, response.status_int)
        nose.tools.assert_in('/user/login?came_from', response.location)



class TestRegroupFields(object):
    def test_regroup_fields(self):
        input_dict = {
            'name-field_a': 'field a',
            'value-field_a': 'a string',
            'name-field-b': 'field b',
            'value-field-b': 1,
            'name-field-c': 'field c',
            'value-field-c': 2,
        }

        expected_output = {
            'field a': 'a string',
            'field b': 1,
            'field c': 2,
        }
        nose.tools.assert_equals(
            sorted(package_controller._regroup_fields(input_dict).items()),
            sorted(expected_output.items()),
        )

    def test_deleted_field(self):
        input_dict = {
            'name-field_a': 'field a',
            'value-field_a': 'a string',
            'name-field-b': 'field b',
            'value-field-b': 1,
            'name-field-c': 'field c',
            'value-field-c': 2,
        }

        expected_output = {
            'field a': 'a string',
            'field b': 1,
        }
        nose.tools.assert_equals(
            sorted(package_controller._regroup_fields(input_dict, deleted='name-field-c').items()),
            sorted(expected_output.items()),
        )


class TestMetadataViewer(custom_helpers.FunctionalTestBaseClass):
    '''Tests for the custom CSV preview and metadata viewer on the resource
    read page.

    '''
    def _create_resource(self, file='test-data/lahmans-baseball-database/ManagersHalf.csv'):
        '''Return a test dataset, resource and resource schema.'''

        dataset = factories.Dataset()
        csv_file = custom_helpers.get_csv_file(file)
        user = factories.User()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
                                              upload=csv_file)
        schema = api.action.resource_schema_show(resource_id=resource['id'])

        return dataset, resource, schema

    def test_csv_preview(self):
        '''Simple test of the custom CSV preview on the resource read page.

        '''
        dataset, resource, _ = self._create_resource()

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html

        table = soup.table  # This assumes the CSV preview is the first table
                            # on the page.

        # Test that the table has the right headers texts.
        headers = table.find_all('th')
        assert len(headers) == 10
        assert [h.text for h in headers] == ['playerID', 'yearID', 'teamID',
                                             'lgID', 'inseason', 'half', 'G',
                                             'W', 'L', 'rank']

        # Test that the headers are linked to the right pages.
        for number, header in enumerate(headers):
            links = header.find_all('a')
            assert len(links) == 1
            link = links[0]
            assert link['href'] == toolkit.url_for(controller='package',
                                                   action='resource_read',
                                                   id=dataset['id'],
                                                   resource_id=resource['id'],
                                                   index=number)

        # Test that a few of the table row values are correct.
        rows = table.find_all('tr')
        definitions = rows[0].find_all('td')
        assert [d.text for d in definitions[:3]] == ['hanlone01', 'hanlone01',
                                                     'vanhage01']
        definitions = rows[3].find_all('td')
        assert [d.text for d in definitions[:3]] == ['NL', 'NL', 'NL']

    def test_csv_preview_active_row(self):
        '''Test the selected row in the CSV preview has CSS class "active".'''

        dataset, resource, _ = self._create_resource()

        # Try a few different row numbers, including the first and the last.
        for row_number in(0, 3, 7, 9):

            response = self.app.get(
                toolkit.url_for(controller='package', action='resource_read',
                                id=dataset['id'], resource_id=resource['id'],
                                index=row_number))

            soup = response.html

            table = soup.table  # This assumes the CSV preview is the first
                                # table on the page.

            active_rows = table.find_all('tr', class_='active')
            assert len(active_rows) == 1, ("There should be one row in the "
                                           "table with the CSS class 'active'")
            active_row = active_rows[0]
            assert active_row == table.find_all('tr')[row_number], (
                "The active row should be the row named in the URL")

    def test_csv_preview_default_active_row(self):
        '''Test that visiting /package/{id}/file/{resource_id} (without a
        /schema/{index} on the end) selects the first row in the CSV preview as
        "active" by default.

        '''
        dataset, resource, _ = self._create_resource()

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html

        table = soup.table  # This assumes the CSV preview is the first
                            # table on the page.

        active_rows = table.find_all('tr', class_='active')
        assert len(active_rows) == 1, ("There should be one row in the "
                                       "table with the CSS class 'active'")
        active_row = active_rows[0]
        assert active_row == table.find_all('tr')[0], (
            "The active row should be the first row")

    def _test_metadata_viewer_contents(self, soup, field):
        '''Test that the given soup contains a metadata viewer div with the
        correct contents for the given resource schema field.

        '''
        # Find the metadata viewer div.
        matches = soup.find_all('div', class_='meta tab-content')
        assert len(matches) == 1
        metadata_viewer = matches[0]

        # Test that the heading has the right text.
        headings = metadata_viewer('h2')
        assert len(headings) == 1
        heading = headings[0]
        assert heading.text == 'Metadata for {field}'.format(
            field=field['name'])

        # Test that the definition list has the right contents.
        dlists = metadata_viewer('dl')
        assert len(dlists) == 1
        dlist = dlists[0]

        dterms = dlist('dt')
        assert [dterm.text for dterm in dterms] == field.keys()

        ddefinitions = dlist('dd')
        assert [dd.text.strip() for dd in ddefinitions] == [
            str(value) for value in field.values()]

    def test_metadata_viewer_with_default_active_row(self):
        '''Test the metadata viewer when visiting
        /package/{id}/file/{resource_id} (without a /schema/{index} on the
        end.

        '''
        dataset, resource, schema = self._create_resource()

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html

        # The metadata viewer should be showing the metadata for the first
        # field.
        self._test_metadata_viewer_contents(soup, schema['fields'][0])

    def test_metadata_viewer_with_different_active_rows(self):
        '''Test that the metadata viewer shows the right metadata when
        different columns are selected.

        '''
        dataset, resource, schema = self._create_resource()

        for index in (0, 3, 7, 9):

            response = self.app.get(
                toolkit.url_for(controller='package', action='resource_read',
                                id=dataset['id'], resource_id=resource['id'],
                                index=index))

            soup = response.html

            # The metadata viewer should be showing the metadata for the right
            # field.
            self._test_metadata_viewer_contents(soup, schema['fields'][index])

    def test_resource_with_no_file(self):
        '''When viewing the page of a resource that has a remote URL instead of
        an uploaded file, a 'No such file or directory' error should be shown
        instead of the CSV preview.

        '''
        dataset = factories.Dataset()
        resource = factories.Resource(dataset=dataset)

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html
        divs = soup('div', class_='ckanext-datapreview')
        assert len(divs) == 1
        div = divs[0]
        assert div.text.strip() == ("Error: There's no uploaded file for this "
                                    "resource")

    def test_non_csv_file(self):
        '''When viewing the page of a resource whose file is not a CSV file,
        an error should be shown instead of the CSV preview.

        '''
        dataset = factories.Dataset()
        non_csv_file = custom_helpers.get_csv_file('test-data/not-a-csv.png')
        user = factories.User()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource = api.action.resource_create(package_id=dataset['id'],
                                              upload=non_csv_file)

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html
        divs = soup('div', class_='ckanext-datapreview')
        assert len(divs) == 1
        div = divs[0]
        assert div.text.strip().startswith('Error: ')

    def test_file_switcher(self):
        '''Simple test that the contents of the file switcher dropdown are
        correct.

        '''
        dataset = factories.Dataset()
        resource_1 = factories.Resource(dataset=dataset)
        resource_2 = factories.Resource(dataset=dataset)
        resource_3 = factories.Resource(dataset=dataset)

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource_1['id']))

        # The dropdown should contain links to the two other files in the
        # package.
        soup = response.html
        links = soup.find('h1', class_='dropdown').find('ul').find_all('a')
        assert len(links) == 2
        assert len([link for link in links if link['href'] ==
                   toolkit.url_for(controller='package', action='resource_read',
                                   id=dataset['id'],
                                   resource_id=resource_2['id'])]) == 1
        assert len([link for link in links if link['href'] ==
                   toolkit.url_for(controller='package', action='resource_read',
                                   id=dataset['id'],
                                   resource_id=resource_3['id'])]) == 1

    def test_file_switcher_only_one_resource(self):
        '''Test that the file switcher dropdown is not shown when the package
        only has one resource.

        '''
        dataset = factories.Dataset()
        resource = factories.Resource(dataset=dataset)

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html
        assert soup.find('h1', class_='dropdown').find('ul') is None, (
            "The file switcher dropdown should not be shown when the file "
            "only has one resource")

    def test_csv_preview_unicode(self):
        '''Upload a unicode csv file, test that it handles unicode '''
        dataset, resource, _ = self._create_resource('test-data/unicode.csv')

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        nose.tools.assert_equals(200, response.status_int)

    def test_primary_key_is_on_page_string(self):
        dataset, resource, schema = self._create_resource()
        helpers.call_action(
            'resource_schema_pkey_create',
            resource_id=resource['id'],
            pkey="playerID"
        )

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html
        nose.tools.assert_true(soup.find(text='Primary Key'))
        pkey = soup.find(id='primary-key')
        nose.tools.assert_true(
            pkey.li.a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource['id'])
        )

        nose.tools.assert_true(pkey.li.a.text, 'playerID')

    def test_primary_key_is_on_page_list(self):
        dataset, resource, schema = self._create_resource()
        helpers.call_action(
            'resource_schema_pkey_create',
            resource_id=resource['id'],
            pkey=["playerID", "teamID"]
        )

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource['id']))

        soup = response.html
        nose.tools.assert_true(soup.find(text='Primary Key'))
        pkey = soup.find(id='primary-key')

        pkeys = pkey.find_all('li')
        nose.tools.assert_true(
            pkeys[0].a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource['id'])
        )
        nose.tools.assert_true(pkeys[0].a.text, 'playerID')
        
        nose.tools.assert_true(
            pkeys[1].a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource['id'])
        )
        nose.tools.assert_true(pkeys[1].a.text, 'teamID')

    def test_foreign_key_is_on_page_string(self):
        dataset = factories.Dataset()
        csv_file0 = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/Master.csv')
        user = factories.User()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource0 = api.action.resource_create(package_id=dataset['id'],
                                              upload=csv_file0)
        schema0 = api.action.resource_schema_show(resource_id=resource0['id'])


        csv_file1 = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/ManagersHalf.csv')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource1 = api.action.resource_create(package_id=dataset['id'],
                                              upload=csv_file1)
        schema1 = api.action.resource_schema_show(resource_id=resource1['id'])

        helpers.call_action(
            'resource_schema_fkey_create',
            field="playerID",
            resource_id=resource1['id'],
            referenced_resource_id=resource0['id'],
            referenced_field="playerID",
        )

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource1['id']))

        soup = response.html
        nose.tools.assert_true(soup.find(text='Foreign Keys'))
        pkey = soup.find(id='foreign-key')
        nose.tools.assert_true(
            pkey.li.a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource0['id'])
        )

        nose.tools.assert_true(pkey.li.a.text, 'playerID')

    def test_foreign_key_is_on_page_list(self):
        dataset = factories.Dataset()
        csv_file0 = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/BattingPost.csv')
        user = factories.User()
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource0 = api.action.resource_create(package_id=dataset['id'],
                                              upload=csv_file0)
        schema0 = api.action.resource_schema_show(resource_id=resource0['id'])


        csv_file1 = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/AllstarFull.csv')
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        resource1 = api.action.resource_create(package_id=dataset['id'],
                                              upload=csv_file1)
        schema1 = api.action.resource_schema_show(resource_id=resource1['id'])

        helpers.call_action(
            'resource_schema_fkey_create',
            field=["playerID", "yearID"],
            resource_id=resource1['id'],
            referenced_resource_id=resource0['id'],
            referenced_field=["playerID", "yearID"],
        )

        response = self.app.get(
            toolkit.url_for(controller='package', action='resource_read',
                            id=dataset['id'], resource_id=resource1['id']))

        soup = response.html
        nose.tools.assert_true(soup.find(text='Foreign Keys'))

        fkey = soup.find(id='foreign-key')
        #check that the name of the referned csv file appears
        nose.tools.assert_true('BattingPost.csv' in fkey.text)

        fkeys = fkey.find_all('li')

        #check the source link
        nose.tools.assert_equals(
            fkeys[0].a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource1['id'])
        )
        nose.tools.assert_equals(fkeys[0].a.text, 'playerID')

        nose.tools.assert_equals(
            fkeys[1].a.attrs['href'],
            '/package/{0}/file/{1}/schema/1'.format(
                dataset['id'], resource1['id'])
        )
        nose.tools.assert_equals(fkeys[1].a.text, 'yearID')

        #check the destination link
        nose.tools.assert_equals(
            fkeys[2].a.attrs['href'],
            '/package/{0}/file/{1}/schema/2'.format(
                dataset['id'], resource0['id'])
        )
        nose.tools.assert_equals(fkeys[2].a.text, 'playerID')
        

        #check the destination link
        nose.tools.assert_equals(
            fkeys[3].a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource0['id'])
        )
        nose.tools.assert_equals(fkeys[3].a.text, 'yearID')
