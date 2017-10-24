class SchemaError(Exception):
    """
    Rasied by Schema.check() - container of multiple error objects.
    """
    def __init__(self, **errors):
        self.errors = errors
        
    def __str__(self):
        return str(self.errors)
        
    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))
        
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
    
class MalformedInteger(SchemaError):
    """
    Raised when an integer cannot be processed from a string, or is otherwise
    improperly formatted.
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