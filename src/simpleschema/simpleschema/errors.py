class SchemaError(Exception):
    """
    Base error for all schema problems.
    """
        
class MissingValue(SchemaError):
    """
    Raised when a value is not provided.
    """

class NotAString(SchemaError):
    """
    Raised when a string is required, but one is not provided.
    """
    
class NotAnInteger(SchemaError):
    """
    Raised when an integer is required, but one is not provided.
    """
    
class NotASequence(SchemaError):
    """
    Raised when a sequence is expected but one is not provided.
    """

class NotAnEmail(SchemaError):
    """
    Raised when a field should contain an valid email address, and it 
    is malformed.
    """

class BadType(SchemaError):
    """
    Raised when the type of the provided value is incorrect.
    """

class OutOfBounds(SchemaError):
    """
    Raised if the given value is outside of the bounds of a given field.
    """

class TooShort(OutOfBounds):
    """
    Raised when a value is too short.
    """

class TooLong(OutOfBounds):
    """
    Raised when a value is too long.
    """
    
class TooSmall(OutOfBounds):
    """
    Raised when a value is not of sufficient quantity.
    """

class TooBig(OutOfBounds):
    """
    Raised when a value is too large.
    """

class BadBoolean(SchemaError):
    """
    Raised when a value cannot be cast to a boolean. 
    """
    
class BadDateFormat(SchemaError):
    """
    Raised when a value cannot be converted into a datetime object. 
    """