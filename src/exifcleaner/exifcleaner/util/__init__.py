"""
Utility classes and functions
"""
from webob import Request, Response
from json import JSONEncoder
import pprint
import random
import udatetime
import itertools

def to_base(num, alpha):
    """
    Take a decimal integer, and encode it into a string using the
    given alphabet. 
    
    The effect is converting the number into a different base.
    
    This function is used for generating non-human readable, one-way,
    small ids. 
    
    If the alphabet is shuffled and multiple numbers are used, the 
    end result is a highly collision-resistant, short identifier.
    """
    base = len(alpha)
    output = []
    while num:
        num, rem = divmod(num, base)
        output.append(alpha[rem])
    output.reverse()
    return "".join(output)

DEFAULT_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEFAULT_SEPARATORS = "-:_"

def too_long(value, max_length=512):
    """
    Return True if the length of value isn't too long.
    """
    if len(value) > max_length:
        return False
    else:
        return True
        
def bool_from_string(value):
    """
    Convert y/n/yes/no/t/f/true/false/0/1 into a boolean.
    
    Integers will be cast to boolean, and follow python conventions
    (0 is False, all other integers are True)
    
    None is considered False.
    """
    if value is None:
        return False
    
    if isinstance(value, int):
        return bool(value)
    
    if isinstance(value, bool):
        return value
        
    if value.lower() in ['0', 'false', 'n', 'f', 'no']:
        return False
    if value.lower() in ['1', 'true', 'y', 'yes']:
        return True
    
    raise ValueError("Boolean value malformed.")

def datetime_from_string(value):
    """
    Given a string that should be an RFC3339 datetime, return a python datetime
    object.
    """
    if isinstance(value, str):
        return udatetime.from_string(value)
    else:
        return value

def random_id(alpha=None):
    """
    Generate a random, non-decodable ID.
    
    Seed is provided to assist with unit testing.
    """
    if alpha is None:
        alpha = DEFAULT_ALPHABET
    
    # shuffle the alphabet
    alpha = random.sample(alpha, len(alpha))
    
    num1 = random.randint(0, 1024)
    num2 = random.randint(0, 1024)
    num3 = random.randint(0, 1024)
    
    output = []
    
    for i in range(0, 3):
        num = random.randint(0, 1024)
        output.append(to_base(num, alpha))
    
    return "".join(output)

class ExifJSONEncoder(JSONEncoder):
    """
    Handle quirks of saving piexif dictionaries as JSON
    """
    def default(self, o):
        if type(o) is bytes:
            try:
                return o.decode("utf-8")
            except UnicodeDecodeError:
                return "XXXXXXXXX"
        else:
            return JSONEncoder.default(self, o)

class UnsetType:
    """
    A holder value, like NoneType, that indicates a value has never been 
    provided before.
    
    Assumed to be a singleton.
    """
    def __str__(self):
        return "UNSET"
        
    def __repr__(self):
        return "UNSET"
        
    def __nonzero__(self):
        return False

UNSET = UnsetType()

def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    
    taken from https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)
    


def string_to_score(string, ignore_case=False):
    """
    From "redis in action": https://redislabs.com/ebook/part-2-core-concepts/chapter-7-search-based-applications/7-2-sorted-indexes/7-2-2-non-numeric-sorting-with-zsets/ 
    """
    
    if ignore_case:
        string = string.lower()
    
    pieces = list(map(ord, string[:6]))
    
    while len(pieces) < 6:
        pieces.append(-1)
    
    score = 0
    
    for piece in pieces:
        score = score * 257 + piece + 1
    
    return score * 2 + (len(string) > 6)
