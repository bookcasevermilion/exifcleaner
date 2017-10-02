from . import manager, errors
from webob import Request, Response
from .. import common

class UserAuthMiddleware:
    def __init__(self, application, redis_url="redis://127.0.0.1:6379", admin=False):
        self.user_manager = manager.UserManager(redis_url=redis_url)
        
    def __call__(self, environ, start_response):
        pass

class UserService(common.BaseService):
    """
    RESTish API for managing users.
    
    Credentials are passed with each request, using HTTP Basic Auth.
    
    /users, GET - list users
    /users, POST - add a new user
    /user/username, PUT - update a user
    /user/username, GET - get a single user
    /user/username, DELETE - remove a user
    /login, POST - authenticate a user
    """
    
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        common.BaseService.__init__(self, redis_url=redis_url)
        
        self.path_map = {
            re.compile("/user/(?P<username>[^/]+)$"): {
                "GET": self.get,
                "DELETE": self.delete,
                "PUT": self.modify
            },
            re.compile("/users/?$"): { 
                "GET": self.listing,
                "POST": self.add
            },
            re.compile("/login/?$"): {
                "POST": self.authenticate
            },
            re.compile("/reset/?$"): {
                "GET": self.reset_request
            },
            re.compile("/reset/(?P<code>[^/]+)$"): {
                "POST": self.reset_password
            }
        }
        
    def add(self, request):
         return Response("Adding a new user.")
    
    def delete(self, request, username):
        return Response("Deleting {}".format(username))
    
    def modify(self, request, username):
        return Response("Modifying {}".format(username))
        
    def listing(self):
        return Response("Listing users")
        
    def get(self, request, username):
        return Response("Getting user {}".format(username))
    
    def reset_request(self, request):
        pass
    
    def password_reset(self, request, code):
        pass
    
    