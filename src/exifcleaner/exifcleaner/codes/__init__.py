"""
Generic Expiring Code Generation Library.

Create and manages single-use codes.
"""

from .. import common
from . import manager
from . import errors

class CodeService(common.BaseService):
    """
    RESTish API for managing single-use codes.
    
    Designed to be subclassed.
    """
    
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        common.BaseService.__init__(self, redis_url=redis_url)
        
        self.codes = manager.CodeManager(redis_url=redis_url)
        
        self.path_map = {
            re.compile("/use/(?P<id>[^/]+)$"): {
                "GET": self.use
            },
            re.compile("/codes/?$"): { 
                "GET": self.listing,
                "POST": self.add
            },
            re.compile("/code/(?P<id>[^/]+)$"): {
                "GET": self.get,
                "DELETE": self.delete
            }
        }
        
    def use(self, request, id):
        user = self.authorize(request, activated=False)
        
        try:
            self.manager.use(code, user.username)
            response = Response()
            response.json_body = True
            return response
        except UserNotFound:
            raise util.web.JSONError(1102)
        except manager.errors.UserMismatch:
            raise util.web.JSONError(1101)
        
    def listing(self, request):
        self.authorize(request, admin=True)
        
        nav = util.pagination.nav(request, self.manager.count())
        
        data = self.manager.codes(start=nav['start'], stop=nav['end'])
        
        del nav['start']
        del nav['end']
        
        response = Response()
        
        base_url = util.web.request_uri(request.environ)
        
        output = {
            'activations': [],
            'pagination': nav
        }
        
        for act in data:
            if act is None:
                output['codes'].append(None)
            else:
                output['codes'].append(act.to_json())
        
        response.json_body = output
        
        return response
        
    def add(self, request):
        self.authorize(request, admin=True)
        
        username = request.POST.get("username", None)
        
        if username is None:
            raise util.web.JSONError(1001)
        
        try:
            code = self.manager.new(username)
        except UserNotFound:
            raise util.web.JSONError(1002)
        
        response = Response()
        response.json_body = code.to_json()
        
        return response
        
    def delete(self, request, id):
        user = self.authorize(request, admin=True)
        
        self.manager.delete(id)
        
        response = Response()
        
        response.json_body = True
        
        return response
        
    def get(self, request, id):
        user = self.authorize(request, admin=True)
        
        response = Response()
        
        code = self.manager.get(id)
        
        response.json_body = code.to_json()
        
        return response