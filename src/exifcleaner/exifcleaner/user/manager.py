"""
Alternate User Manager
"""

import redis
from schema import Schema, And, Use, Optional
import udatetime
import datetime
from passlib.hash import pbkdf2_sha256
from . import errors
from .. import util

USER_INDEX_KEY = "index:users-main"
USERS_BY_USERNAME = "index:users:by-username"

def if_none_generate_id(value):
    if value is None or "":
        return util.random_id()
    else:
        return value

add_schema = Schema({
    "email": str,
    Optional('admin', default=False): And(Use(util.bool_from_string), bool),
    Optional('activated', default=False): And(Use(util.bool_from_string), bool),
    Optional('enabled', default=False): And(Use(util.bool_from_string), bool),
    Optional('id'): str,
    "username": And(str, util.too_long),
    "password": And(str, util.too_long),
    # TODO: this is wrong - the default time is not right.
    Optional('joined', default=udatetime.now()): And(Use(util.datetime_from_string), datetime.datetime)
})

modify_schema = Schema({
    Optional("email"): str,
    Optional('admin'): And(Use(util.bool_from_string), bool),
    Optional('activated'): And(Use(util.bool_from_string), bool),
    Optional('enabled'): And(Use(util.bool_from_string), bool),
    Optional('id'): str,
    Optional("username"): And(str, util.too_long),
    Optional("password"): And(str, util.too_long),
    Optional('joined'): And(Use(util.datetime_from_string), datetime.datetime)
})

redis_schema = Schema({
    "email": str,
    'admin': And(Use(util.bool_from_string), bool),
    'activated': And(Use(util.bool_from_string), bool),
    'enabled': And(Use(util.bool_from_string), bool),
    'id': str,
    "username": And(str, util.too_long),
    "password": And(str, util.too_long),
    'joined': And(Use(util.datetime_from_string), datetime.datetime)
})

class User:
    """
    Simple encapsulation of the data that makes up a user. 
    
    Does validation and can marshal back and fourth to/from a redis data 
    strcutre
    """
    
    def __init__(self, **attributes):
        """
        Create a user object. 
        """
        self._old = {
            "email": util.UNSET,
            'admin': util.UNSET,
            'activated': util.UNSET,
            'enabled': util.UNSET,
            'id': util.UNSET,
            "username": util.UNSET,
            "password": util.UNSET,
            'joined': util.UNSET
        }
        
        # parsed_attributes = modify_schema.validate(attributes)
        
        self.update(**attributes)
    
    def old(self, attr):
        """
        Return the previous value for the given attribute.
        """
        return self._old[attr]
    
    def __setattr__(self, attr, value):
        """
        Overloading __setattr__ to record the previous value of attributes as 
        they are applied.
        """
        if not attr.startswith("_"):
            try:
                self._old[attr] = getattr(self, attr)
            except AttributeError:
                self._old[attr] = util.UNSET
            
        object.__setattr__(self, attr, value)
    
    def changed(self):
        """
        Return a list of which attributes have changed.
        """
        changed = []
        for key, value in self._old.items():
            if value is not util.UNSET and getattr(self, key) != value:
                changed.append(key)
                
        return changed
    
    @property
    def key(self):
        """
        Getter to prefix the user ID for use as a redis key.
        """
        return "user:{}".format(self.id)
    
    @property
    def password(self):
        return self._password
        
    @password.setter
    def password(self, value):
        """
        Overload the setter for password so only a hash is stored inside the object.
        """
        self._password = pbkdf2_sha256.hash(value)
    
    def _update(self, **attributes):
        """
        Helper function for populating attributes of this object from keyword
        arguments.
        """
        for key, value in attributes.items():
            setattr(self, key, value)
    
    def update(self, **attributes):
        """
        Update and verify attributes supplied as keyword arguments.
        """
        data = modify_schema.validate(attributes)
        self._update(**data)
    
    @classmethod
    def from_redis(cls, data):
        """
        Construct a User object from a dictionary retrieved from Redis.
        """
        data = redis_schema.validate(data)
        
        # password is already encrypted, bypass setter.
        password = data['password']
        del data['password']
        
        obj = cls(**data)
        obj._password = password
        
        return obj
    
    def to_redis(self):
        """
        Representation of this User as a dictionary, ready for insertion into
        Redis.
        
        Does a special schema validation to ensure the data is sound.
        """
        output = {
            'email': self.email,
            'username': self.username,
            'joined': udatetime.to_string(self.joined), 
            'enabled': int(self.enabled),
            'id': self.id
        }
        
        output['password'] = self.password
        output['admin'] = int(self.admin)
        output['activated'] = int(self.activated)
        
        # double check if the data is legit
        redis_schema.validate(output)
        
        return output
        
    def authenticate(self, password, bypass_activation=False):
        """
        Return True if the plaintext password matches the password
        for this user.
        
        Set bypass_activation to True to allow the user to authenticate
        so they can activate their account.
        """
        if not self.activated and not bypass_activation:
            return False
        
        return bool(pbkdf2_sha256.verify(password, self.password))
        
    def __str__(self):
        return "id={}, username={}, admin={}, activated={}".format(
            self.id, 
            self.username, 
            self.admin, 
            self.activated)
        
    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))

class UserManager:
    """
    CRUD for working with users. Most methods return a User object. 
    """
    
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        self.connection = redis.StrictRedis.from_url(redis_url, decode_responses=True, encoding='utf-8')
        
    def save(self, user):
        """
        Save a user object.
        """
        with self.connection.pipeline() as pipe:
            pipe.hmset(user.key, user.to_redis())
            if "username" in user.changed():
                pipe.hdel(USER_INDEX_KEY, user.old("username"))
                
            pipe.zadd(USERS_BY_USERNAME, util.string_to_score(user.username), user.key)
            pipe.hset(USER_INDEX_KEY, user.username, user.key)
            pipe.execute()
        
    def add(self, **attributes):
        """
        Create a new User in the database.
        """
        if "id" not in attributes:
            attributes['id'] = util.random_id()
        
        data = add_schema.validate(attributes)
        
        user = User(**data)
        
        if self.exists(user.username):
            raise errors.UsernameInUse()
        
        self.save(user)
        
        return user
        
    def get(self, username):
        """
        Retrieve a user from the database, by username.
        """
        user_key = self.connection.hmget(USER_INDEX_KEY, username)[0]
        
        if user_key:
            data = self.connection.hgetall(user_key)
            
            if data:
                return User.from_redis(data)
            else:
                raise errors.UserNotFound()
        else:
            raise errors.UserNotFound()
    
    def exists(self, username):
        """
        Return True if the username is in the system. False if not.
        """
        return bool(self.connection.hexists(USER_INDEX_KEY, username))
    
    def authenticate(self, username, password):
        """
        Given the username/password, return True if the username/password match,
        False if they do not.
        """
        try:
            user = self.get(username)
        except errors.UserNotFound:
            return False
        
        return user.authenticate(password)
        
    def activate(self, username):
        """
        Activate a user.
        """
        user = self.modify(username, activated=True)
        return user
    
    def delete(self, username):
        """
        Remove a user from the database.
        """
        user = self.get(username)
        
        with connection.pipeline() as pipe:
            pipe.delete(user.key)
            pipe.hdel(USER_INDEX_KEY, user.username)
            pipe.zrem(USERS_BY_USERNAME, user.key)
            pipe.execute()
            
        return None
    
    def modify(self, un, **attributes):
        """
        Modify one or more attributes of a user.
        """
        existing = self.get(un)
        
        if 'username' in attributes and attributes['username'] != existing.username:
            if self.exists(attributes['username']):
                raise errors.UsernameInUse()
                
        
        existing.update(**attributes)
        
        self.save(existing)
        
        return existing
        
    def users(self, start=0, stop=-1):
        """
        Return a listing of users.
        """
        users = self.connection.zrange(USERS_BY_USERNAME, start, stop)
        
        output = []
        
        with self.connection.pipeline() as pipe:
            for user_key in users:
                pipe.hgetall(user_key)
                
            results = pipe.execute()
            
            for result in results:
                output.append(User.from_redis(result))
        
        return output
        