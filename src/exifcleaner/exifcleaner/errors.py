"""
General Application Exceptions
"""

class ExifCleanerError(Exception):
    """
    All classes derive from this one.
    """
    
class ExifCleanerConfigError(ExifCleanerError):
    """
    Raised when something is misconfigured.
    """
    
class ExifCleanerTooManyRetries(ExifCleanerError):
    """
    Raised when there are too many retries; generating an ID,
    talking to a remote system, etc.
    """
    
class ExifCleanerNotAJPEG(ExifCleanerError):
    """
    Raised when the file uploaded is not a JPEG.
    """
    
class ExifCleanerInputError(ExifCleanerError):
    """
    Generic class for any input errors
    """
    
# Mapping of error codes to example human-readable strings
codes = {
    1001: "Adding activation: Username must be provided",
    1002: "Adding activation: User not found",
    1101: "Activating: User mismatch",
    1102: "Activating: User not found",
    1201: "Bad page number",
    1202: "Bad per-page value"
}
    