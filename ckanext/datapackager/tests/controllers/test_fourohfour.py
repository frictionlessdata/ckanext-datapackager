'''Functional tests for controllers/fourohfour.py.'''

import ckanext.datapackager.tests.helpers as helpers


class TestDataPackager404Controller(helpers.FunctionalTestBaseClass):
    '''Functional tests for the DataPackager404Controller class.'''

    def test_dataset_search(self):
        '''CKAN's default dataset search page should be a 404.'''

        self.app.get('/dataset', status=404)
        self.app.get('/package', status=404)
