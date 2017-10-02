from exifcleaner.errors import ExifCleanerInputError, ExifCleanerError

class CodeNotFound(ExifCleanerError):
    """
    An code code was not valid.
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
    
class CodeAlreadyUsed(ExifCleanerError):
    """
    The code being consumed has already been used.
    """