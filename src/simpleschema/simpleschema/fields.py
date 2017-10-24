"""
A collection of common fields.
"""

from . import errors
from .unset import UNSET
import udatetime
import datetime

class SchemaField:
    def __init__(self, required=True, default=None, parser=None, type=None, validator=None):
        self.required = required
        self.default = default
        
        # if a default is given, the field is no longer required.
        if self.default is not None:
            self.required = False
        
        self.type = type
        self.parser = parser
        
        if validator is not None:
            self.validator = validator
        
    def _typecheck(self, value):
        if self.type is not None:
            return isinstance(value, self.type)
            
        return True
    
    def _parser(self, value):
        if self.parser is not None:
            return self.parser(value)
            
        return value
        
    def __call__(self, value=UNSET):
        if value is UNSET and self.default is not None:
            if callable(self.default):
                value = self.default()
            else:
                value = self.default
        
        if self.required and value is UNSET:
            raise errors.MissingValue()
        
        value = self._parser(value)
        if not self._typecheck(value):
            raise errors.BadType()
        
        if hasattr(self, "validator"):
            value = self.validator(value)
        
        return value

class StringField(SchemaField):
    def __init__(self, min=1, max=255, **kwargs):
        self.min = min
        self.max = max
        SchemaField.__init__(self, **kwargs)
        
    def validator(self, value):
        if not isinstance(value, str):
            raise errors.NotAString()
            
        if len(value) < self.min:
            raise errors.TooShort()
            
        if len(value) > self.max:
            raise errors.TooLong()
            
        return value

class RFC3339DateField(SchemaField):
    """
    Schema field that can be provided with a datetime object, or
    a RFC3339-formatted datetime. 
    """
    def validator(self, value):
        if isinstance(value, datetime.datetime):
            return value
        elif isinstance(value, str):
            try:
                return udatetime.from_string(value)
            except ValueError:
                raise errors.BadDateFormat()
        else:
            raise errors.BadType()
            

class EmailField(StringField):
    def __init__(self, max=320, **kwargs):
        kwargs['max'] = max
        StringField.__init__(self, **kwargs)
        
    def validator(self, value):
        value = StringField.validator(self, value)
        
        if not "@" in value:
            raise errors.NotAnEmail()
            
        return value
        
class DelimitedListField(SchemaField):
    """
    Field for lists of values, separated by some delimiter (default is |).
    
    Overloads the type=, validator=, and parser= keyword arguments - in the case
    of DelimitedListField, these arguments are applied to each element of the 
    list during validation.
    
    The processed list of values will contain error objects in place of individual
    processed values if an error occurred with that value.
    
    Unique arguments:
        - min: the minimum length of the list, after processing.
        - max: the maximum length of the list, after processing.
        - omit_empty: remove any items that are empty strings or None.
        - delimiter: when the value is a string, the delimiter is used to split
                     the string into individual values.
        - strip: boolean, string, or callable. 
                 If boolean, True means the values are stripped. 
                 False, they are not. 
                 
                 If string, the given characters are stripped (passed to strip())
                 
                 If callable, each value is passed to the callable before any 
                 other processing.
    """
    def __init__(self, delimiter="|", min=None, max=None, strip=True, omit_empty=False, type=None, validator=None, parser=None, **kwargs):
        self.delimiter = delimiter
        self.list_validator = validator
        self.list_type = type
        self.list_parser = parser
        self.strip = strip
        self.omit_empty = omit_empty
        self.min = min
        self.max = max
        
        kwargs['validator'] = None
        kwargs['type'] = None
        kwargs['parser'] = None
        
        SchemaField.__init__(self, **kwargs)
        
    def split(self, value):
        """
        Split a string - provied here for easy overloading for more
        complex splitting operations.
        """
        return value.split(self.delimiter)
    
    def _strip(self, value):
        """
        Perform trim/stripping logic. 
        
        Broken out for easier overloading, and to keep process() simple.
        """
        if callable(self.strip):
            value = self.strip(value)
        elif isinstance(self.strip, str):
            value = value.strip(self.strip)
        elif self.strip is True:
            value = value.strip()
            
        return value
    
    def process(self, value):
        """
        Run the value through the list parser, type check, and validator,
        if any were provided.
        """
        if isinstance(value, str) and self.strip:
            value = self._strip(value)
        
        if self.list_parser is not None:
            value = self.list_parser(value)
            
        if self.list_type is not None:
            if not isinstance(value, self.list_type):
                raise errors.BadType()
                
        if self.list_validator is not None:
            value = self.list_validator(value)
            
        return value
        
    def validator(self, value):
        if isinstance(value, str):
            value = self.split(value)
        
        if not isinstance(value, (list, set, frozenset, range, tuple)):
            raise errors.NotASequence()
        
        output = []
        
        for item in value:
            try:
                processed = self.process(item)
                
                if self.omit_empty and (processed is None or processed == ''):
                    continue
                
                output.append(processed)
            except Exception as e:
                output.append(e)
        
        if self.min is not None and len(output) < self.min:
            raise errors.TooShort()
            
        if self.max is not None and len(output) > self.max:
            raise errors.TooLong()
        
        return output
    
        
class IntegerField(SchemaField):
    """
    Field for integer values. Can work from a string.
    
    Unique arguments:
        - min: the integer must be higher than this (negative OK)
        - max: the integer must be lower than this (negative OK)
    
    """
    def __init__(self, min=None, max=None, **kwargs):
        self.min = min
        self.max = max
        
        SchemaField.__init__(self, **kwargs)
    
    def validator(self, value):
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise errors.MalformedInteger()
        
        if not isinstance(value, int):
            raise errors.NotAnInteger()
        
        if self.min is not None and value < self.min:
            raise errors.TooSmall()
            
        if self.max is not None and value > self.max:
            raise errors.TooBig()
        
        return value
        
class BooleanField(SchemaField):
    """
    Represents a True/False value.
    
    Can take sring input, where the following rules apply:
        
        - 'y', 'yes', '1', 't', 'true' are True (case insensative)
        - 'n', 'no', '0', 'f', 'false' are False (case insensative)
        
    Raises simpleschema.errors.BadBoolean if the value doesn't conform
    to the above rules.
    """
    def validator(self, value):
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.lower()
            
            if value in ['1', 'y', 'yes', 't', 'true']:
                return True
            elif value in ['0', 'n', 'no', 'f', 'false']:
                return False
            else:
                raise errors.BadBoolean()
        elif isinstance(value, int):
            return bool(value)
        else:
            raise errors.BadBoolean()
            
        