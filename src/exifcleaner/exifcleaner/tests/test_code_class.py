"""
Tests For The Code Manager - Code class
"""
import pytest
import udatetime, datetime
from exifcleaner import util
import simpleschema

@pytest.fixture(autouse=True)
def fixate_randomness(monkeypatch):
    """
    Set well-known values for time and ramdomness-sensative
    functions.
    """
    monkeypatch.setattr("udatetime.now", lambda: udatetime.from_string('1993-10-26T08:00:00-04:00'))
    monkeypatch.setattr(util, "random_id", lambda: "test-code-1")

def test_basic_construction_no_params():
    """
    Ensure typical case construction of a Code object functions properly - 
    all default parameters.
    """
    from exifcleaner.codes.manager import Code
    c = Code(user="testuser1")
    
    assert c.user == "testuser1"
    assert c.code == "test-code-1"
    assert c.created == udatetime.from_string('1993-10-26T08:00:00-04:00')
    assert c.expires == 3600
    assert c.used is False
    assert c.key == "code:test-code-1"
    assert c.expires_at() == udatetime.from_string('1993-10-26T09:00:00-04:00')
    
def test_from_redis():
    """
    Test the from_redis() class method.
    """
    from exifcleaner.codes.manager import Code
    
    data = {
        'user': 'test-user-2',
        'code': 'code-1-2-3',
        'created': '2010-11-03T10:00:00-04:00',
        'used': '1',
        'expires': '3423'
    }
    
    c = Code.from_redis(data)
    
    assert c.user == "test-user-2"
    assert c.code == "code-1-2-3"
    assert c.created == udatetime.from_string('2010-11-03T10:00:00-04:00')
    assert c.expires == 3423
    assert c.used is True
    assert c.key == "code:code-1-2-3"
    assert c.expires_at() == udatetime.from_string('2010-11-03T10:57:03.000000-04:00')
    
import pytest
@pytest.mark.parametrize("test_input,error", [
    ({'user':""}, {'user': simpleschema.errors.TooShort}),
    ({'user':453}, {'user': simpleschema.errors.NotAString}),
    ({'user':"x"*400}, {'user': simpleschema.errors.TooLong}),
    ({'expires': "sadas1234"}, 
        {'expires': simpleschema.errors.MalformedInteger, 
         'user': simpleschema.errors.MissingValue}),
])
def test_creation_bad_input(test_input, error):
    """
    Throw some bad data at the constructor
    """
    from exifcleaner.codes.manager import Code
    
    with pytest.raises(simpleschema.errors.SchemaError) as err:
        c = Code(**test_input)
        
    for key, val in err.value.errors.items():
        assert isinstance(val, error[key])
        
def test_creation_everything_wrong():
    """
    Make a mistake with every field.
    """
    from exifcleaner.codes.manager import Code
    
    expected = {
        'user': simpleschema.errors.TooLong,
        'code': simpleschema.errors.TooShort,
        'created': simpleschema.errors.BadDateFormat,
        'used': simpleschema.errors.BadBoolean,
        'expires': simpleschema.errors.NotAnInteger
    }
    
    with pytest.raises(simpleschema.errors.SchemaError) as err:
        c = Code(
            user="x"*999,
            code="",
            created="asdf dsfsdfasdfasdfsdfsd",
            used="X",
            expires=None)
        
    for key, val in err.value.errors.items():
        assert isinstance(val, expected[key])