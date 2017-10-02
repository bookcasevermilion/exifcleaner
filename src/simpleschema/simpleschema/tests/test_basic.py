"""
Basic test cases for Simple Schema.
"""

import unittest
from unittest.mock import patch
import simpleschema
import udatetime
import datetime
import inspect

class BadPassword(simpleschema.errors.SchemaError):
    pass

def password_check(value):
    """
    Password must contain at least one special character. 
    """
    special = "~!@#$%^&*()"
    
    if set(value) & set(special):
        return value
    else:
        raise BadPassword()

class TestSchemaBase(unittest.TestCase):
    def compare_lists(self, output, expected):
        """
        Verify that all of the members of output match whats in expected.
        
        If a member of expected is a class, verify that the corresponding member
        of output is of that type.
        """
        for index, value in enumerate(expected):
            subject = output[index]
            
            if inspect.isclass(value):
                self.assertTrue(isinstance(subject, value))
            else:
                self.assertEqual(subject, value)
    
    def static_date(self):
        """
        Return a known datetime object.
        """
        return udatetime.from_string('1993-10-26T08:00:00-04:00')
        
    def validate_to_dict(self, generator):
        """
        Convert the output of Schema.validate into a dictionary.
        """
        return dict([x for x in generator])
        
    def compare_errors(self, schema_output, expected):
        """
        Compare the output of a vall to Schema.validate() to a dictionary.
        
        In the case of the value at a given key in the expected dict being a class,
        instead of checking for equilivence, we instead ensure the value in the
        validator result is an instance of that class.
        """
        for field, result in schema_output.items():
            test = expected[field]
            
            if inspect.isclass(test):
                self.assertTrue(isinstance(result, test))
            else:
                self.assertEqual(test, result)
        
    
    def schema(self):
        """
        Construct a non-trivial test schema.
        """
        schema = simpleschema.Schema()
        
        schema['email'] = simpleschema.fields.EmailField()
        schema['username'] = simpleschema.fields.StringField(min=10, max=40)
        schema['password'] = simpleschema.fields.StringField(min=5, validator=password_check)
        schema['active'] = simpleschema.fields.BooleanField(default=True)
        schema['last-visit'] = simpleschema.fields.RFC3339DateField(default=self.static_date)
        
        return schema
    

class TestBasicSchema(TestSchemaBase):
    
    def test_happy_path_all_good(self):
        """
        Typical use case example - no errors
        """
        schema = self.schema()
        
        data = {
            'email': "none@donthave.com",
            'password': "NCQurep@ssw0rd",
            'active': False,
            'username': "myusername",
            'last-visit': '2001-09-26T08:00:00-04:00'
        }
        
        expected = {
            'username': "myusername",
            'email': "none@donthave.com",
            'password': "NCQurep@ssw0rd",
            'active': False,
            'last-visit': udatetime.from_string(data['last-visit'])
        }
        
        self.assertEqual(schema.validict(data), expected)
        
    def test_happy_path_no_values(self):
        """
        Typical use case example - no values provided.
        """
        schema = self.schema()
        
        expected = {
            'username': simpleschema.errors.MissingValue,
            'password': simpleschema.errors.MissingValue,
            'email': simpleschema.errors.MissingValue,
            'active': True,
            'last-visit': self.static_date()
        }
        
        self.compare_errors(schema.validict({}), expected)
                
                
    def test_check_method_no_errors(self):
        schema = self.schema()
        
        data = {
            'email': "none@donthave.com",
            'password': "NCQurep@ssw0rd",
            'active': False,
            'username': "myusername",
            'last-visit': '2001-09-26T08:00:00-04:00'
        }
        
        expected = {
            'username': "myusername",
            'email': "none@donthave.com",
            'password': "NCQurep@ssw0rd",
            'active': False,
            'last-visit': udatetime.from_string(data['last-visit'])
        }
        
        self.assertEqual(schema.validict(data), expected)
                
    def test_check_method_errors(self):
        """
        When running the Schema.check() method with improper data, 
        it should raise SchemaError.
        """
        schema = self.schema()
        
        self.assertRaises(simpleschema.SchemaError, schema.check, {})
    
    def test_check_method_errors_verify(self):
        """
        Verify that SchemaError has the expected errors within it.
        """
        schema = self.schema()
        
        expected = {
            'username': simpleschema.errors.MissingValue,
            'password': simpleschema.errors.MissingValue,
            'email': simpleschema.errors.MissingValue
        }
        
        try:
            schema.check({})
        except simpleschema.SchemaError as e:
            self.compare_errors(e.errors, expected)

class TestRigidSchema(TestSchemaBase):
    """
    Test the RigidSchema class
    """
    
    def test_happy_path(self):
        """
        Typical use case, no errors.
        """
        schema = simpleschema.RigidSchema(self.schema())
        
        data = {
            'email': "none@donthave.com",
            'password': "NCQurep@ssw0rd",
            'active': "0",
            'username': "myusername",
            'last-visit': '2001-09-26T08:00:00-04:00'
        }
        
        expected = {
            'username': "myusername",
            'email': "none@donthave.com",
            'password': "NCQurep@ssw0rd",
            'active': False,
            'last-visit': udatetime.from_string(data['last-visit'])
        }
        
        self.assertEqual(schema.validict(data), expected)
        
    def test_happy_path_errors(self):
        """
        Typical use case, but values are omitted, and errors are present.
        """
        schema = simpleschema.RigidSchema(self.schema())
        
        data = {
            'username': "myusername",
            'password': "NCQurepsswrd",
            'active': "0"
        }
        
        expected = {
            'username': "myusername",
            'password': BadPassword,
            'active': False,
            'last-visit': simpleschema.errors.MissingValue,
            'email': simpleschema.errors.MissingValue
        }
        
        self.compare_errors(schema.validict(data), expected)   

    def test_no_values(self):
        """
        All values omitted.
        """
        schema = simpleschema.RigidSchema(self.schema())
        
        expected = {
            'username': simpleschema.errors.MissingValue,
            'password': simpleschema.errors.MissingValue,
            'active': simpleschema.errors.MissingValue,
            'last-visit': simpleschema.errors.MissingValue,
            'email': simpleschema.errors.MissingValue
        }
        
        self.compare_errors(schema.validict({}), expected)  

class TestFlexiSchema(TestSchemaBase):
    """
    Test the FlexiSchema class
    """
    
    def test_happy_path(self):
        """
        Typical use case, some values omitted.
        """
        schema = simpleschema.FlexiSchema(self.schema())
        
        data = {
            'username': "myusername",
            'password': "NCQurep@ssw0rd",
            'active': False
        }
        
        expected = {
            'username': "myusername",
            'password': "NCQurep@ssw0rd",
            'active': False,
        }
        
        self.assertEqual(schema.validict(data), expected)
        
    def test_happy_path_errors(self):
        """
        Typical use case, errors, but values are omitted.
        """
        schema = simpleschema.FlexiSchema(self.schema())
        
        data = {
            'username': "myusername",
            'password': "NCQurepsswrd",
            'active': False
        }
        
        expected = {
            'username': "myusername",
            'password': BadPassword,
            'active': False,
        }
        
        self.compare_errors(schema.validict(data), expected)   

    def test_no_values(self):
        """
        All values omitted.
        """
        schema = simpleschema.FlexiSchema(self.schema())
        
        self.assertEqual(schema.validict({}), {})  

class TestSchemaFieldBase(TestSchemaBase):
    """
    Test functionality of the SchemaField base class.
    """
    
    def test_validator_noerror(self):
        """
        Test the validator= keyword argument, no error.
        """
        
        field = simpleschema.fields.SchemaField(validator=password_check)
        
        self.assertEqual("mypass!", field("mypass!"))
    
    def test_validator_unset(self):
        """
        Test the validator= keyword argument, no value provided
        """
        
        field = simpleschema.fields.SchemaField(validator=password_check)
        
        self.assertRaises(simpleschema.errors.MissingValue, field)
    
    def test_validator_baddefault(self):
        """
        Test the validator= keyword argument - bad default provided
        """
        
        field = simpleschema.fields.SchemaField(validator=password_check, default="nospecial")
        
        self.assertRaises(BadPassword, field)
    
    def test_validator_default(self):
        """
        Test the validator= keyword argument - default provided
        """
        
        field = simpleschema.fields.SchemaField(validator=password_check, default="hithere!")
        
        self.assertEqual(field(), "hithere!")
    
    def test_validator_error(self):
        """
        Test the validator= keyword argument - error state.
        """
        
        field = simpleschema.fields.SchemaField(validator=password_check)
        
        self.assertRaises(BadPassword, field, "nospecialchars")
    
    def test_validator_with_typecheck(self):
        """
        Test the validator= keyword, combined with type=
        """
        field = simpleschema.fields.SchemaField(validator=password_check, type=str)
        
        self.assertRaises(simpleschema.errors.BadType, field, 1.0)
        
    
    def test_validator_with_parser(self):
        """
        Test the validator= keyword with the parser= keyword.
        """
        field = simpleschema.fields.SchemaField(validator=password_check, parser=lambda x: x.lower())
        
        self.assertEqual(field("BAHAHAH!!AHAHA"), "bahahah!!ahaha")
        
    def test_validator_with_badparser(self):
        """
        Test the validator= keyword with the parser= keyword, parser returns invalid data.
        """
        field = simpleschema.fields.SchemaField(
            validator=password_check, 
            parser=lambda x: "nospecial")
        
        self.assertRaises(BadPassword, field, "bahahah!!ahaha")
        
    def test_parser_and_typecheck(self):
        """
        Test combining the parser= and type= keyword arguments
        """
        
        field = simpleschema.fields.SchemaField(
            parser=lambda x: str(x),
            type=str)
        
        self.assertEqual(field(12.32), "12.32")
        
    def _derived_class(self, error=None):
        """
        Generate a derived class from SchemaField. 
        
        Validation will always return the value ver batim.
        
        If error is set, it is expected to be an exception class to raise instead.
        """
        class MyField(simpleschema.fields.SchemaField):
            def validator(self, value):
                if error is not None:
                    raise error()
                
                return value
                
        return MyField
        
    def test_overload_validator(self):
        """
        If deriving a class from SchemaField, ensure it is called.
        """
        class_ = self._derived_class()
        
        field = class_()
        
        self.assertEqual(field("called?"), "called?")
    
    def test_overload_validator_with_default(self):
        """
        Derived class, default keyword in use
        """
        class_ = self._derived_class()
        
        field = class_(default="hello")
        
        self.assertEqual(field(), "hello")
    
    def test_overload_validator_with_type(self):
        """
        Derived class, default keyword in use
        """
        class_ = self._derived_class()
        
        field = class_(type=str)
        
        self.assertRaises(simpleschema.errors.BadType, field, 1.0)
        
    def test_overload_validator_with_parser(self):
        """
        Derived class, parser keyword in use
        """
        class_ = self._derived_class()
        
        field = class_(parser=lambda x: "lower")
        
        self.assertEqual(field("whatever"), "lower")
        
    def test_overload_validator_with_validator_keyword(self):
        """
        Derived class, validator keyword in use
        """
        class_ = self._derived_class()
        
        field = class_(validator=lambda x: "lower")
        
        self.assertEqual(field("whatever"), "lower")
        
class TestDelimitedListField(TestSchemaBase):
    """
    Test the DelimitedListField.
    """
    
    def typical(self, **params):
        """
        Return a typically populated field. Can add your own params if you want.
        """
        usual = {
            'min': 1,
            'max': 20,
            'default':"  hello |    world",
            'type':str,
            'parser':lambda x: x.upper()
        }
        
        usual.update(params)
        
        field = simpleschema.fields.DelimitedListField(**usual)
        
        return field
    
    def test_happy_path(self):
        field = self.typical()
        
        data = "first  |  \t  second||  third|fourth|eighth"
        
        expected = [
            'FIRST', 'SECOND', '', 'THIRD', 'FOURTH', 'EIGHTH'
        ]
        
        self.assertEqual(field(data), expected)
    
    def test_happy_path_too_short(self):
        """
        Typical use, but the parsed list has too few items in it. 
        """
        
        field = self.typical(omit_empty=True, min=4)
        
        self.assertRaises(simpleschema.errors.TooShort, field, "one|two|three||")
    
    def test_happy_path_too_long(self):
        field = self.typical()
        
        data = "first  |  \t  second||  third|fourth|eighth"*10
        
        self.assertRaises(simpleschema.errors.TooLong, field, data)
    
    def test_omit_empty(self):
        """
        Remove empty members.
        """
        field = simpleschema.fields.DelimitedListField(omit_empty=True)
        
        data = "one|||two"
        
        expected = ["one", "two"]
        
        self.assertEqual(field(data), expected)
        
    def test_validator(self):
        """
        Use the validator= keyword argument.
        """
        def validator(value):
            value = int(value)
            return value
        
        field = simpleschema.fields.DelimitedListField(validator=validator)
        
        data = "2|3 |4|5|alpha|beta"
        
        expected = [2, 3, 4, 5, ValueError, ValueError]
        
        self.compare_lists(field(data), expected)
    
    def test_default_badvalue(self):
        """
        Use the default= keyword argument, but the default doesn't validate.
        """
        field = simpleschema.fields.DelimitedListField(
            default=[1, 3, 3, "4"], 
            type=int)
        
        expected = [1, 3, 3, simpleschema.errors.BadType]
        
        self.compare_lists(field(), expected)
    
    def test_default(self):
        """
        Use the default= keyword argument.
        """
        field = simpleschema.fields.DelimitedListField(default="1 | 3 | 3 | four")
        
        expected = ['1', '3', '3', "four"]
        
        self.compare_lists(field(), expected)
    
    def test_type_check(self):
        """
        Use the type= keyword argument.
        """
        field = simpleschema.fields.DelimitedListField(type=int)
        
        data = [1, 2, 3, 4, "abc"]
        
        expected = [1, 2, 3, 4, simpleschema.errors.BadType]
        
        self.compare_lists(field(data), expected)
        
class TestBooleanField(TestSchemaFieldBase):
    
    def test_default(self):
        """
        Ensure that when a default is set, it is used.
        """
        field = simpleschema.fields.BooleanField(default=False)
        
        self.assertEqual(field(), False)
        
      
    