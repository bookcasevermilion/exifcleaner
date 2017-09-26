from . import manager, errors
from webob import Request, Response

class UserAuthMiddleware:
    def __init__(self, application, redis_url="redis://127.0.0.1:6379", admin=False):
        self.user_manager = manager.UserManager(redis_url=redis_url)
        
    def __call__(self, environ, start_response):
        pass

class UserAPI:
    """
    RESTish API for managing users.
    
    Credentials are passed with each request, using HTTP Basic Auth.
    
    /users, GET - list users
    /users, POST - add a new user
    /users/username, PUT - update a user
    /users/username, GET - get a single user
    /users/username, DELETE - remove a user
    /login, POST - validate a user
    /activate/activation_id, GET - activate the user who has provided credentials
    """
    
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        self.user_manager = manager.UserManager(redis_url=redis_url)
        
    def __call__(self, environ, start_response):
        """
        Routing
        """
        request = Request(environ)
        
        
        
        
    def add(self, request):
        pass
    
    def delete(self, request):
        pass
    
    def activate(self, request):
        pass
    
    def modify(self, request):
        pass
    
    def password_reset(self, request):
        pass
    
    