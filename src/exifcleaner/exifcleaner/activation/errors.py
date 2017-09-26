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
    
# Mapping of error codes to example human-readable strings
codes = {
    1001: "Adding activation: Username must be provided",
    1002: "Adding activation: User not found",
    1101: "Activating: User mismatch",
    1102: "Activating: User not found",
    1201: "Listing: bad page number",
    1202: "Listing: bad per-page value"
}