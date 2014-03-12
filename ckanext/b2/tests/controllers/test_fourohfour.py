'''Functional tests for controllers/fourohfour.py.'''

import ckanext.b2.tests.helpers as helpers


class TestB2FourOhFourController(helpers.FunctionalTestBaseClass):
    '''Functional tests for the B2404Controller class.'''

    def test_dataset_search(self):
        '''CKAN's default dataset search page should be a 404.'''

        self.app.get('/dataset', status=404)
        self.app.get('/package', status=404)
