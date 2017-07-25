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