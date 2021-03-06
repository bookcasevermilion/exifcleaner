from exifcleaner.errors import ExifCleanerInputError, ExifCleanerError

class ActivationNotFound(ExifCleanerError):
    """
    An activation code was not valid.
    """
    
class FailedAuthentication(ExifCleanerError):
    """
    Authentication failed.
    """
    
class UserMismatch(ExifCleanerError):
    """
    The user authenticated OK, but the code they provided was created for
    a different user.
    """