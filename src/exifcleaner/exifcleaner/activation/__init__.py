"""
Account activation code management.
"""
from . import manager
from .. import util
from ..user.manager import UserManager
from ..user.errors import UserNotFound
from webob import Request, Response
import base64
import re
from schema import Schema, Optional, And, Use, SchemaError

def str_to_int(value):
    return int(value)

pagination = Schema({
   Optional("per-page", default=20): And(Use(str_to_int), lambda x: 0 < x < 100, int, error=1201),
   Optional("page", default=1): And(Use(str_to_int), lambda x: x > 0, int, error=1202)
})

class ActivationService:
    """
    RESTish web service that manages activation codes.
    
    End-User Functions
    ------------------
    /activate/[code] - GET, activate the given code. User must be authenticated.
    
    Administration Functions
    ------------------------
    /activations - GET, list activations. Pagination provided in the output.
    /activations - POST, add a new activation. Returns newly created activation info.
    /activation/[code] - PUT, modify an existing activation.
    /activation/[code] - GET, retrieve activation info.
    /activation/[code] - DELETE, remove an activation.
    """
    
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        self.manager = manager.ActivationManager(redis_url=redis_url)
        self.users = UserManager(redis_url=redis_url) 
        
        self.path_map = {
            re.compile("/activate/(?P<code>[^/]+)$"): {
                "GET": self.activate
            },
            re.compile("/activations/?$"): { 
                "GET": self.listing,
                "POST": self.add
            },
            re.compile("/activation/(?P<code>[^/]+)$"): {
                "GET": self.get,
                "DELETE": self.delete
            }
        }
        
    def __call__(self, environ, start_response):
        request = Request(environ)
        
        response = None
        
        print(request.path)
        
        try:
            for regexp, method_mapping in self.path_map.items():
                match = re.match(regexp, request.path)
                
                if match:
                    print(match.groupdict())
                    
                    for http_method, method in method_mapping.items():
                        print("METHOD: ", http_method)
                        print("CALLABLE: ", method)
                        print("REQ METHOD: ", request.method)
                        if http_method == request.method:
                            response = method(request, **match.groupdict())
                            return response(environ, start_response)
                    else:
                        if request.method not in ["GET", "HEAD"]:
                            raise util.web.BadRequest("Method not supported", code=405)
                        else:
                            raise util.web.BadRequest()
            else:
                raise util.web.NotFound()
            
        except manager.errors.ActivationNotFound:
            r = util.web.NotFound()
            return r(environ, start_response)
        except util.web.BadRequest as r:
            return r(environ, start_response)
        
    def authorize(self, request, activated=True, admin=False):
        """
        Authorize the given request using basic auth.
        
        Returns a User object representing the user credntials provided.
        """
        if request.authorization:
            auth_type, hashed_pass = request.authorization
            
            decoded = base64.b64decode(hashed_pass)
            
            username, password = decoded.decode('utf-8').split(':')
            
            print(decoded)
            
            try:
                user = self.users.get(username)
                
                if admin and not user.admin:
                    raise util.web.Unauthorized()
                
                if not user.authenticate(password, bypass_activation=(not activated)):
                    raise util.web.Unauthorized()
                else:
                    return user
            except UserNotFound:
                raise util.web.Unauthorized()
        else:
            raise util.web.Unauthorized()
            
    def activate(self, request, code):
        user = self.authorize(request, activated=False)
        
        try:
            self.manager.activate(code, user.username)
            response = Response()
            response.json_body = True
            return response
        except UserNotFound:
            raise util.web.JSONError(1102)
        except manager.errors.UserMismatch:
            raise util.web.JSONError(1101)
        
    def listing(self, request):
        self.authorize(request, admin=True)
        
        try:
            nav = pagination.validate(request.GET.mixed())
        except SchemaError as e:
            import ipdb; ipdb.set_trace()
            raise
        
        print(nav)
        
        per_page = nav['per-page']
        page = nav['page']
        
        start = (page*per_page) - per_page
        end = (page*per_page) - 1
        
        count = self.manager.count()
        
        next = page + 1
        previous = page - 1
        
        if end > count:
            next = None
        
        if page == 1:
            previous = None
        
        data = self.manager.activations(start=start, stop=end)
        
        response = Response()
        
        output = {
            'activations': [],
            'pagination': {
                'count': count,
                'previous': previous,
                'next': next
            }
        }
        
        for act in data:
            if act is None:
                output['activations'].append(None)
            else:
                output['activations'].append(act.to_json())
        
        response.json_body = output
        
        return response
        
    def add(self, request):
        self.authorize(request, admin=True)
        
        username = request.POST.get("username", None)
        
        if username is None:
            raise util.web.JSONError(1001)
        
        try:
            activation = self.manager.new(username)
        except UserNotFound:
            raise util.web.JSONError(1002)
        
        response = Response()
        response.json_body = activation.to_json()
        
        return response
        
    def delete(self, request, code):
        user = self.authorize(request, admin=True)
        
        self.manager.delete(code)
        
        response = Response()
        
        response.json_body = True
        
        return response
        
    def get(self, request, code):
        user = self.authorize(request, admin=True)
        
        response = Response()
        
        activation = self.manager.get(code)
        
        response.json_body = activation.to_json()
        
        return response