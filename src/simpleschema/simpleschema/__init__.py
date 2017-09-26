"""
Simple Schema.

Yet another schema description/validation framework.
"""

from . import unset
from . import errors
from . import fields
        
class Schema:
    def __init__(self, fields=None):
        if fields is None:
            fields = {}
        
        self._fields = fields
        
    def __getitem__(self, key):
        return self._fields[key]
        
    def __setitem__(self, key, value):
        print(key, value)
        self._fields[key] = value
        
    def __delitem__(self, key):
        del self._fields[key]
        
    def validate(self, data):
        for name, field in self._fields.items():
            value = data.get(name, unset.UNSET)
            
            if value is unset.UNSET and not field.default and field.required is False:
                continue
            
            try:
                yield name, field(value)
            except errors.SchemaError as e:
                yield name, e