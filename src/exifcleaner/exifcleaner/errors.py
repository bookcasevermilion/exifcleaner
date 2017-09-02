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