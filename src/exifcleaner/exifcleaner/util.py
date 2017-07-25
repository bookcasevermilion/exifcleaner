"""
Utility classes and functions
"""
from webob import Request, Response
from json import JSONEncoder

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
    

class BadRequest(Exception):
    """
    WSGI App/Exception hybrid. 
    
    Generic catch-all for any bad request.
    """
    
    def __init__(self, msg="Bad Request", code=400):
        self.msg = msg
        self.code = code
        
    def __str__(self):
        return self.msg
        
        
    def __call__(self, environ, start_response):
        response = Response(self.msg, status=self.code)
        return response(environ, start_response)
    
class NotFound(BadRequest):
    """
    Raised when something is not found. (404 Not Found)
    """
    def __init__(self, msg="Not Found", code=404):
        BadRequest.__init__(self, msg, code)

class Redirect(BadRequest):
    """
    Raised when we need to redirect the client to another url within our app.
    
    TODO: handle SSL?
    """
    def __init__(self, path, code=302):
        self.path = path
        self.code = code
        
    def __call__(self, environ, start_response):
        url = 'http://%s%s' % (environ['HTTP_HOST'], self.path)
        
        response = Response(url, status=self.code)
        
        response.headers['location'] = url
        
        return response(environ, start_response)
        
