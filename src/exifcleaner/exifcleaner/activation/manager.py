"""
Manage user activation codes.
"""

import redis
from .. import user
from .. import util
from . import errors
import udatetime
import datetime

ACTIVATION_BY_DATE = "index:activations:newest-first"

class Activation:
    def __init__(self, user, code=None, created=None, expires=None):
        self.user = user
        
        if created is None:
            created = udatetime.now()
        
        if expires is None:
            expires = datetime.timedelta(hours=1).seconds
            
        if code is None:
            code = util.random_id()
            
        self.code = code
        self.created = created
        self.expires = expires
    
    @classmethod
    def prefix(cls, code):
        return "act:{}".format(code)
    
    @property
    def key(self):
        return Activation.prefix(self.code)
    
    def expires_at(self):
        """
        Return the datetime when this activation expires.
        """
        diff = datetime.timedelta(seconds=self.expires)
        return self.created + diff
        
    @classmethod
    def from_redis(cls, data):
        user = data['user']
        created = udatetime.from_string(data['created'])
        expires = int(data['expires'])
        code = data['code']
        
        obj = cls(user=user, code=code, created=created, expires=expires)
        
        return obj
        
    def to_redis(self):
        return {
            'user': self.user,
            'code': self.code,
            'created': udatetime.to_string(self.created)
        }
        
    def to_json(self):
        """
        Return a parsed dictionary that is JSON compatible.
        """
        return {
            'user': self.user,
            'code': self.code,
            'created': udatetime.to_string(self.created),
            'expires_at': udatetime.to_string(self.expires_at()),
            'expires': self.expires
        }


class ActivationManager:
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        self.connection = redis.StrictRedis.from_url(redis_url, decode_responses=True, encoding='utf-8')
        self.user_manager = user.manager.UserManager(redis_url=redis_url)
        
    def new(self, username):
        user = self.user_manager.get(username)
        
        activation = Activation(user=user.id)
        
        with self.connection.pipeline() as pipe:
            pipe.hmset(activation.key, activation.to_redis())
            pipe.expire(activation.key, activation.expires)
            pipe.lpush(ACTIVATION_BY_DATE, activation.code)
            pipe.execute()
            
        return activation
        
    def get(self, code):
        key = Activation.prefix(code)
        
        with self.connection.pipeline() as pipe:
            pipe.hgetall(key)
            pipe.ttl(key)
            results = pipe.execute()
        
        if not results[0]:
            raise errors.ActivationNotFound()
            
        data = results[0]
        data['expires'] = results[1]
        
        activation = Activation.from_redis(data)
        
        return activation
        
    def exists(self, code):
        key = Activation.prefix(code)
        
        return bool(self.connection.exists(key))
        
    def delete(self, code):
        key = Activation.prefix(code)
        
        if not self.exists(code):
            raise errors.ActivationNotFound()
        
        with self.connection.pipeline() as pipe:
            pipe.delete(key)
            pipe.lrem(ACTIVATION_BY_DATE, 0, code)
            pipe.execute()
            
        
    def activate(self, code, username, password=None):
        user = self.user_manager.get(username)
        
        if password is not None:
            if not user.authenticate(password):
                raise errors.FailedAuthentication()
                
        activation = self.get(code)
        
        if activation.user != user.id:
            raise errors.UserMismatch()
        
        # TODO: find a way to do this using the manager methods
        with self.connection.pipeline() as pipe:
            pipe.hset(user.key, "activated", "1")
            pipe.delete(activation.key)
            pipe.lrem(ACTIVATION_BY_DATE, 0, code)
            pipe.execute()
                
    def count(self):
        """
        Return the total number of activations
        """
        return self.connection.llen(ACTIVATION_BY_DATE)
                
    def activations(self, start=0, stop=-1):
        activations = self.connection.lrange(ACTIVATION_BY_DATE, start, stop)
        
        output = []
        
        with self.connection.pipeline() as pipe:
            for code in activations:
                key = Activation.prefix(code)
                pipe.hgetall(key)
                pipe.ttl(key)
                
            results = pipe.execute()
            
            for data, ttl in util.grouper(results, 2):
                if data:
                    data['expires'] = ttl
                    output.append(Activation.from_redis(data))
                else:
                    output.append(None)
                
        return output
                
            
        