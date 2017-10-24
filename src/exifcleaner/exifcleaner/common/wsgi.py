from exifcleaner import util
from exifcleaner.user.manager import UserManager

class BaseService:
    """
    Common functionality for all services. 
    
    Contains authentication mechanism, as well as
    basic routing.
    
    Derived classes should have an instance variable called
    "path_map" where keys are regular expressions that match
    against the request URI. Members are dictionaries where keys
    are the type of HTTP request (GET, POST, etc), and each member
    is a callable.
    
    Callables take a Request object, and any keyword data extracted
    from the request URI. They are expected to return a Response 
    object, or raise a BadRequest exception.
    """
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        self.redis_url = redis_url
        self.users = UserManager(redis_url=redis_url)
        self.path_map = {}
        
        
    def __call__(self, environ, start_response):
        request = Request(environ)
        
        response = None
        
        try:
            for regexp, method_mapping in self.path_map.items():
                match = re.match(regexp, request.path)
                
                if match:
                    for http_method, method in method_mapping.items():
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