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


class TestDataPackagerAuthorizationShow(custom_helpers.FunctionalTestBaseClass):
    def test_anonymous_users_can_view_packages(self):
        package = factories.Dataset(user=factories.User())
        response = self.app.get('/package/{0}'.format(package['name']))
        nose.tools.assert_equals(200, response.status_int)

    def test_users_can_view_other_users_packages(self):
        package = factories.Dataset(user=factories.User())

        other_user = factories.User()
        extra_environ = {'REMOTE_USER': str(other_user['name'])}

        response = self.app.get('/package/{0}'.format(package['name']),
                                extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)

    def test_sysadmins_can_view_other_users_packages(self):
        package = factories.Dataset(user=factories.User())

        other_user = factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(other_user['name'])}

        response = self.app.get('/package/{0}'.format(package['name']),
                                extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)


class TestDataPackagerAuthorizationCreate(custom_helpers.FunctionalTestBaseClass):
    def test_anonymous_users_cannot_create_packages(self):
        response = self.app.get('/package/new')
        nose.tools.assert_equals(302, response.status_int)
        nose.tools.assert_equals(
            'http://localhost/user/login?came_from=http://localhost/package/new',
            response.location
        )

    def test_users_can_create_package(self):
        user = factories.User()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        response = self.app.get('/package/new', extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)

    def test_sysadmins_can_create(self):
        user = factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        response = self.app.get('/package/new', extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)


class TestDataPackagerAuthorizationUpdate(custom_helpers.FunctionalTestBaseClass):
    def test_user_can_update_packages_they_created(self):
        user = factories.User()
        package = factories.Dataset(user=user)

        extra_environ = {'REMOTE_USER': str(user['name'])}

        response = self.app.get('/package/edit/{0}'.format(package['name']),
                                extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)

    def test_user_cannot_update_someone_elses_package(self):
        package = factories.Dataset(user=factories.User())

        other_user = factories.User()
        extra_environ = {'REMOTE_USER': str(other_user['name'])}

        response = self.app.get('/package/edit/{0}'.format(package['name']),
                                extra_environ=extra_environ, expect_errors=True)
        nose.tools.assert_equals(401, response.status_int)

    def test_anonynmous_user_cannot_update_packages(self):
        package = factories.Dataset(user=factories.User())

        response = self.app.get('/package/edit/{0}'.format(package['name']),
                                expect_errors=True)
        nose.tools.assert_equals(302, response.status_int)
        nose.tools.assert_equals(
            'http://localhost/user/login?came_from=http://localhost/package/edit/{0}'.format(package['name']),
            response.location
        )

    def test_sysadmins_can_update_all_packages(self):
        sysadmin = factories.Sysadmin()
        package = factories.Dataset(user=factories.User())

        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        response = self.app.get('/package/edit/{0}'.format(package['name']),
                                extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)


class TestDataPackagerAuthorizationDelete(custom_helpers.FunctionalTestBaseClass):
    def test_user_cannot_delete_someone_elses_package(self):
        package = factories.Dataset(user=factories.User())

        other_user = factories.User()
        extra_environ = {'REMOTE_USER': str(other_user['name'])}

        response = self.app.get('/package/delete/{0}'.format(package['name']),
                                extra_environ=extra_environ, expect_errors=True)
        nose.tools.assert_equals(401, response.status_int)

    def test_sysadmin_can_delete_anyones_package(self):
        package = factories.Dataset(user=factories.User())

        sysadmin = factories.Sysadmin()
        extra_environ = {'REMOTE_USER': str(sysadmin['name'])}

        response = self.app.get('/package/delete/{0}'.format(package['name']),
                                extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)

    def test_users_can_delete_packages_they_created(self):
        user = factories.Sysadmin()
        package = factories.Dataset(user=user)

        extra_environ = {'REMOTE_USER': str(user['name'])}

        response = self.app.get('/package/delete/{0}'.format(package['name']),
                                extra_environ=extra_environ)
        nose.tools.assert_equals(200, response.status_int)


class TestMetadataViewer(custom_helpers.FunctionalTestBaseClass):
    '''Tests for the custom CSV preview and metadata viewer on the resource
    read page.

    '''
    def _create_resource(self, file='test-data/lahmans-baseball-database/ManagersHalf.csv'):
        '''Return a test dataset, resource and resource schema.'''

        user = factories.User()
        dataset = factories.Dataset(user=user)
        csv_file = custom_helpers.get_csv_file(file)
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
        assert [h.text.strip() for h in headers] == [
            'playerID', 'yearID', 'teamID', 'lgID', 'inseason', 'half', 'G',
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
        assert heading.text.strip() == 'Metadata for {field}'.format(
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
        user = factories.User()
        dataset = factories.Dataset(user=user)
        non_csv_file = custom_helpers.get_csv_file('test-data/not-a-csv.png')
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
        nose.tools.assert_true(soup.find(text='Primary key'))
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
        nose.tools.assert_true(soup.find(text='Primary key'))
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
        user = factories.User()
        dataset = factories.Dataset(user=user)
        csv_file0 = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/Master.csv')
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
        nose.tools.assert_true(soup.find(text='Foreign keys'))
        pkey = soup.find(id='foreign-key')
        nose.tools.assert_true(
            pkey.li.a.attrs['href'],
            '/package/{0}/file/{1}/schema/0'.format(
                dataset['id'], resource0['id'])
        )

        nose.tools.assert_true(pkey.li.a.text, 'playerID')

    def test_foreign_key_is_on_page_list(self):
        user = factories.User()
        dataset = factories.Dataset(user=user)
        csv_file0 = custom_helpers.get_csv_file(
            'test-data/lahmans-baseball-database/BattingPost.csv')
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
        nose.tools.assert_true(soup.find(text='Foreign keys'))

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


class TestMetadataEditor(custom_helpers.FunctionalTestBaseClass):
    '''Frontend tests for the custom resource edit form.'''

    # TODO: Test that edit button isn't shown and editor doesn't load if user
    # isn't authorized.

    def _setup(self):
        '''Create some test objects that a lot of test methods below use.'''

        user = factories.User()
        dataset = factories.Dataset(user=user)
        api = ckanapi.TestAppCKAN(self.app, apikey=user['apikey'])
        csv_file = _get_csv_file(
            '../test-data/lahmans-baseball-database/PitchingPost.csv')
        resource = api.action.resource_create(package_id=dataset['id'],
                                              upload=csv_file)
        schema = api.action.resource_schema_show(resource_id=resource['id'])

        # Get the resource edit page.
        extra_environ = {'REMOTE_USER': str(user['name'])}
        response = self.app.get(toolkit.url_for(controller='ckanext.datapackager.controllers.package:DataPackagerPackageController',
                                                action='resource_edit',
                                                id=dataset['id'],
                                                resource_id=resource['id']),
                                extra_environ=extra_environ)

        return dataset, user, api, resource, schema, response

    def _preview_table(self, response):
        return response.html.find(class_='ckanext-datapreview').find('table')

    def _metadata_editor(self, response):
        return response.html.find(class_='ckanext-datapreview').find(
            class_='meta')

    def _metadata_editor_fieldset(self, response):
        fieldsets = self._metadata_editor(response)('fieldset')
        return [fieldset for fieldset in fieldsets
                if 'active' in fieldset.get('class', '')][0]

    def _click_on_column(self, index, response, extra_environ=None):

        # Find the button for going to the requested column.
        table = self._preview_table(response.html)
        row = table.find_all('tr')[index]
        button = row.find('button')

        # Click the button.
        return response.forms[0].submit(button['name'],
                                        extra_environ=extra_environ)

    def test_default_selected_column(self):
        '''Test the contents of the metadata editor with the default column
        selected.

        When you first load the metadata editor page, the first column should
        be selected in the CSV preview and shown in the metadata editor.

        '''
        _, _, _, _, schema, response = self._setup()

        # The first row in the CSV preview should have CSS class "active".
        soup = response.html
        table = self._preview_table(soup)
        first_row = table.find('tr')
        assert 'active' in first_row['class']

        # The metadata editor should show only the metadata for the first
        # column.
        editor = self._metadata_editor(soup)
        fieldsets = editor.find_all('fieldset')
        assert 'active' in fieldsets[0]['class']
        for fieldset in fieldsets[1:]:
            assert 'active' not in fieldset.get('class', '')

        # Test that the contents of the metadata editor are correct.
        fieldset = fieldsets[0]  # All the editor contents are in the fieldset.

        # The title in the metadata editor should have the right field name.
        assert fieldset.find('legend').text.strip() == (
            'Metadata for {name}'.format(name=schema['fields'][0]['name']))

        # The "name: " <input> in the metadata editor should be pre-filled with
        # the right field's name.
        name_input = fieldset.find(id='schema-0-name')
        assert name_input['value'] == schema['fields'][0]['name']

        # The "type: " <select> in the metadata editor should be pre-selected
        # to the right field's type.
        type_select = fieldset.find(id='schema-0-type')

        # The <select> should have one <option> whose value matches the
        # field's type, and that option should be selected.
        selected_options = type_select('option',
                                       value=schema['fields'][0]['type'])
        assert len(selected_options) == 1
        assert 'selected' in selected_options[0].attrs

        # All <options> whose value doesn't match the field's type should not
        # be selected.
        unselected_options = [
            option for option in type_select('option')
            if option['value'] != schema['fields'][0]['type']]
        for option in unselected_options:
            assert 'selected' not in option.attrs

    def test_changing_selected_column(self):
        _, _, _, _, schema, response = self._setup()

        # We'll test clicking no the 2nd, 5th and last columns.
        for column_index in (1, 4, len(schema['fields']) - 1):

            response = self._click_on_column(column_index, response)

            # Only the right row in the CSV preview should have CSS class
            # "active".
            soup = response.html
            table = self._preview_table(soup)
            for index, row in enumerate(table.find_all('tr')):
                if index == column_index:
                    assert 'active' in row['class']
                else:
                    assert 'active' not in row.get('class', '')

            # The metadata editor should show only the metadata for the right
            # column.
            editor = self._metadata_editor(soup)
            fieldsets = editor.find_all('fieldset')
            for index, fieldset in enumerate(fieldsets):
                if index == column_index:
                    assert 'active' in fieldset['class']
                else:
                    assert 'active' not in fieldset.get('class', '')

            # Test that the contents of the metadata editor fieldset are right.
            fieldset = fieldsets[column_index]

            # The title in the metadata editor should have the right field name
            assert fieldset.find('legend').text.strip() == (
                'Metadata for {name}'.format(
                    name=schema['fields'][column_index]['name']))

            # The "name: " <input> in the metadata editor should be pre-filled
            # with the right field's name.
            name_input = fieldset.find(
                id='schema-{column_index}-name'.format(
                    column_index=column_index))
            assert name_input['value'] == (
                schema['fields'][column_index]['name'])

            # The "type: " <select> in the metadata editor should be
            # pre-selected to the right field's type.
            type_select = fieldset.find(
                id='schema-{column_index}-type'.format(
                    column_index=column_index))

            # The <select> should have one <option> whose value matches the
            # field's type, and that option should be selected.
            selected_options = type_select(
                'option', value=schema['fields'][column_index]['type'])
            assert len(selected_options) == 1
            assert 'selected' in selected_options[0].attrs

            # All <options> whose value doesn't match the field's type should
            # not be selected.
            unselected_options = [
                option for option in type_select('option')
                if option['value'] != schema['fields'][column_index]['type']]
            for option in unselected_options:
                assert 'selected' not in option.attrs

    def test_user_values_persist_when_changing_columns(self):
        '''If the user enters or selects anything in the form and then clicks
        to go to a different column, they should be able to go back to the
        previous column and their input should still be there.

        '''
        _, _, api, resource, original_schema, response = self._setup()

        # Go to column 2, change some of the form values, go to column 4,
        # change some values, go back to column 2 and check that our changed
        # values are still there, then go back to column 4 and check that our
        # values are still there.
        response = self._click_on_column(2, response)
        response.forms[0]['schema-2-name'] = 'foo'
        response.forms[0]['schema-2-type'] = 'integer'
        response = self._click_on_column(4, response)
        response.forms[0]['schema-4-name'] = 'bar'
        response = self._click_on_column(2, response)
        assert response.forms[0]['schema-2-name'].value == 'foo'
        assert response.forms[0]['schema-2-type'].value == 'integer'
        response = self._click_on_column(4, response)
        assert response.forms[0]['schema-4-name'].value == 'bar'

        # Our changes should not have been saved in the db yet.
        schema = api.action.resource_schema_show(resource_id=resource['id'])
        assert schema == original_schema

    def test_rename_resource(self):
        '''Test that renaming a resource works and doesn't break anything.

        (For example, renaming a resource should not delete its schema!)

        '''
        _, user, api, resource, _, response = self._setup()

        form = response.forms[0]
        form['name'] = 'changed'
        extra_environ = {'REMOTE_USER': str(user['name'])}
        form.submit('save', extra_environ=extra_environ)

        resource = api.action.resource_show(id=resource['id'])
        assert resource['name'] == 'changed'

    def test_edit_one_field(self):
        '''Load the metadata editor, edit one schema field, save it.'''

        _, user, api, resource, _, response = self._setup()

        form = response.forms[0]
        # Change the name of the first column.
        form['schema-0-name'] = 'changed'
        extra_environ = {'REMOTE_USER': str(user['name'])}
        form.submit('save', extra_environ=extra_environ)

        field = api.action.resource_schema_field_show(
            resource_id=resource['id'], index=0)
        assert field['name'] == 'changed'

    def test_edit_another_column(self):
        '''Load the metadata editor, click on one of the columns, edit some of
        its fields, save it.'''

        _, user, api, resource, _, response = self._setup()

        # Find and click the button for the "IPouts" column.
        response.forms[0].submit('go-to-column-12')

        # Change a couple of the IPouts column's fields and save.
        form = response.forms[0]
        form['schema-12-min'] = '50'
        form['schema-12-mean'] = '50'
        extra_environ = {'REMOTE_USER': str(user['name'])}
        form.submit('save', extra_environ=extra_environ)

        field = api.action.resource_schema_field_show(
            resource_id=resource['id'], index=12)
        assert field['name'] == 'IPouts'
        # FIXME: The values have been turned into strings here, they should
        # sill be ints, this is a bug.
        assert field['min'] == '50'
        assert field['mean'] == '50'

    def test_edit_multiple_columns(self):
        '''Edit metadata attributes of multiple columns at once and then save.

        '''
        _, user, api, resource, original_schema, response = self._setup()

        response = self._click_on_column(2, response)
        response.forms[0]['schema-2-name'] = 'foo'
        response.forms[0]['schema-2-type'] = 'integer'
        response = self._click_on_column(4, response)
        response.forms[0]['schema-4-name'] = 'bar'

        extra_environ = {'REMOTE_USER': str(user['name'])}
        response.forms[0].submit('save', extra_environ=extra_environ)

        schema = api.action.resource_schema_show(resource_id=resource['id'])
        for index, field in enumerate(schema['fields']):
            if index == 2:
                assert field['name'] == 'foo'
                assert field['type'] == 'integer'
            elif index == 4:
                assert field['name'] == 'bar'
                assert field['type'] == original_schema['fields'][4]['type']
            else:
                # FIXME: We should be able to assert this, but we can't because
                # all the attribute values get turned into strings when you
                # click Save. This is a bug.
                #assert field == original_schema['fields'][index]
                pass

    def test_error_when_moving_between_columns(self):
        '''If you enter an invalid value then try to move to another column,
        it should reload the same column and show you an error.'''

        _, user, _, _, _, response = self._setup()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        response = self._click_on_column(2, response,
                                         extra_environ=extra_environ)
        response.forms[0]['schema-2-name'] = ''  # An invalid name.
        response = self._click_on_column(4, response,
                                         extra_environ=extra_environ)

        fieldset = self._metadata_editor_fieldset(response)
        name_input = fieldset.find('input', id='schema-2-name')
        error_block = fieldset.find(class_='error-block')
        assert error_block.text.strip() == 'Missing value'
        # The error block should be next to the "name: " <input>
        assert name_input in [s for s in error_block.previous_siblings]

    def test_error_when_saving(self):
        '''If you enter an invalid value then try to save, it should reload the
        same column and show you an error.'''

        _, user, _, _, _, response = self._setup()
        extra_environ = {'REMOTE_USER': str(user['name'])}

        response = self._click_on_column(2, response,
                                         extra_environ=extra_environ)
        response.forms[0]['schema-2-name'] = ''  # An invalid name.
        response = response.forms[0].submit('save',
                                            extra_environ=extra_environ)

        fieldset = self._metadata_editor_fieldset(response)
        name_input = fieldset.find('input', id='schema-2-name')
        error_block = fieldset.find(class_='error-block')
        assert error_block.text.strip() == 'Missing value'
        # The error block should be next to the "name: " <input>
        assert name_input in [s for s in error_block.previous_siblings]

    # TODO: Test deleting attributes from multiple columns at once and then
    # saving. Currently it's hard to write tests because all of the delete
    # buttons have the same name (which may not be valid HTML).

    # TODO: Test adding attributes to multiple columns at once and then saving.
    # Currently it's hard to write tests because all of the add buttons have
    # the same name (which may not be valid HTML).

    # TODO: Test that if you enter text into the add attribute <input>s but
    # don't click add, then go to another column, then go back to the first
    # column, your text is still there waiting to be added.

    # TODO: Test that you can't add an attribute with an empty key.

    # TODO: Test adding an attribute then deleting it again before hitting
    # save.

    # TODO: One big test, do everything at once.
