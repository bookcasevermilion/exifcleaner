from webob import Request, Response
from wsgiref.util import request_uri, guess_scheme, application_uri
from urllib.parse import urljoin

class BadRequest(Exception):
    """
    Raised when something bad happened in a request
    """
    
    def __init__(self, msg="Bad Request", code=400):
        self.msg = msg
        self.code = code
        
    def __str__(self):
        return self.msg
        
        
    def __call__(self, environ, start_response):
        res = Response(self.msg, status=self.code)
        return res(environ, start_response)
    
class NotFound(BadRequest):
    """
    Raised when something is not found.
    """
    def __init__(self, msg="Not Found"):
        BadRequest.__init__(self, msg, code=404)

class Redirect(BadRequest):
    def __init__(self, path, code=302):
        self.path = path
        self.code = code
        
    def __call__(self, environ, start_response):
        base = application_uri(environ)
        
        url = urljoin(base, self.path)
        
        res = Response(url, status=self.code)
        
        res.headers['location'] = url
        
        return res(environ, start_response)
        
class BackEndTrouble(BadRequest):
    def __init__(self, msg="Some trouble with the back-end. Please try your request again later", code=400):
        BadRequest.__init__(self, msg, code)
        
class Unauthorized(BadRequest):
    """
    Raised when a bad content type is specified by the client.
    """
    def __init__(self, msg="Unauthorized", code=401, realm="Exif Cleaner"):
        BadRequest.__init__(self, msg, code)
        self.realm = realm
        
    def __call__(self, environ, start_response):
        res = Response(self.msg, status=self.code)
        res.headers['www-authenticate'] = 'Basic realm={}'.format(self.realm)
        
        return res(environ, start_response)
        
class JSONError(BadRequest):
    """
    Raised when a client makes an error; returns a JSON body containing 
    information about the error.
    """
    
    def __init__(self, errno, error=None, code=400):
        self.code = code
        self.errno = errno
        
    def __call__(self, environ, start_response):
        res = Response(status=self.code)
        output = {
            'errno': self.errno
        }
        
        res.json_body = output
        
        return res(environ, start_response)
    
