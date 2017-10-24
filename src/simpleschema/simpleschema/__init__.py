"""
Simple Schema.

Yet another schema description/validation framework.
"""
import copy
from . import unset
from . import errors
from . import fields

class Schema:
    def __init__(self, fields=None):
        self._fields = {}
        
        if isinstance(fields, Schema):
            for name, field in fields.items():
                self._fields[name] = copy.copy(field)
        elif fields is not None:
            self._fields = fields.copy()
        
    def __getitem__(self, key):
        return self._fields[key]
        
    def __setitem__(self, key, value):
        self._fields[key] = value
        
    def __delitem__(self, key):
        del self._fields[key]
    
    def items(self):
        return self._fields.items()
    
    def validict(self, data):
        """
        Validate the given data, but then return a 
        dictionary of field/processed-or-error pairs.
        """
        return dict([x for x in self.validate(data)])
        
    def check(self, data):
        """
        Raise SchemaError containing all found errors, if any occur.
        """
        _errors = {}
        output = {}
        
        for name, result in self.validate(data):
            if isinstance(result, Exception):
                _errors[name] = result
            else:
                output[name] = result
                
        if _errors:
            raise errors.SchemaError(**_errors)
            
        return output
        
    def validate(self, data):
        
        for name, field in self._fields.items():
            value = data.get(name, unset.UNSET)
            
            if value is unset.UNSET and field.default is unset.UNSET and field.required is False:
                continue
            
            try:
                yield name, field(value)
            except errors.SchemaError as e:
                yield name, e
                
                
class FlexiSchema(Schema):
    """
    A schema where none of the fields are required, and defaults don't apply.
    
    Used for variable keyword updates.
    """
    def validate(self, data):
        for name, field in self._fields.items():
            value = data.get(name, unset.UNSET)
            
            # just skip it if it's not provided.
            if value is unset.UNSET:
                continue
            else:
                try:
                    yield name, field(value)
                except errors.SchemaError as e:
                    yield name, e
                    
                    
class RigidSchema(Schema):
    """
    A schema where all fields are required, and defaults are ignored.
    
    Used primarily for validating marshalled data.
    """
    def validate(self, data):
        for name, field in self._fields.items():
            value = data.get(name, unset.UNSET)
            
            field.required = True
            field.default = None
            
            try:
                yield name, field(value)
            except errors.SchemaError as e:
                yield name, e