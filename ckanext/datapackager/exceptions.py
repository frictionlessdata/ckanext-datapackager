'''All custom exception types used by this extension are defined in one place
here in this module.

'''
class InvalidResourceIDException(Exception):
    '''The exception type that is raised when an invalid resource ID is passed
    to an action function.

    '''
    pass


class ResourceFileDoesNotExistException(Exception):
    '''The exception that's raised when trying to get the path to a resource's
    file in the FileStore, if that resource doesn't have a file in the
    FileStore.

    '''
    pass


class CouldNotReadCSVException(Exception):
    '''The exception that's raised when trying to read a CSV file fails for
    some reason (e.g. it's a corrupt file, not a CSV file, etc).

    '''
    pass
