'''Test helper functions and classes.'''

import os


def get_csv_file(relative_path):
    csv_file = open(fixture_path(relative_path), 'rb')
    return csv_file


def fixture_path(path):
    path = os.path.join(os.path.split(__file__)[0], 'test-data', path)
    return os.path.abspath(path)
