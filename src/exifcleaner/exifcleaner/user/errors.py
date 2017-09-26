from exifcleaner.errors import ExifCleanerInputError, ExifCleanerError

class UserNotFound(ExifCleanerError):
    """
    A user could not be found in the database.
    """
    
class UsernameInUse(ExifCleanerError):
    """
    A username is already in use.
    """