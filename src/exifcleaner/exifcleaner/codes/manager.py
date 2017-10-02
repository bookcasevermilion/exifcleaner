"""
Code Manager - Low-level back end library for creating and managing
single-use codes tied to a user account.

The code must be redeemed by the user provided when created.
"""

import redis
import udatetime
import datetime
from .. import user
from .. import util
from . import errors

class Code:
    def __init__(self, user, code=None, created=None, expires=None, used=False):
        self.user = user
        self.used = used
        
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
        return "code:{}".format(code)
    
    @property
    def key(self):
        return Code.prefix(self.code)
    
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
        used = util.bool_from_string(data['used'])
        
        obj = cls(user=user, code=code, created=created, expires=expires)
        
        return obj
        
    def to_redis(self):
        output = {
            'user': self.user,
            'code': self.code,
            'created': udatetime.to_string(self.created)
        }
        
        if self.used:
            output['used'] = '1'
        else:
            output['used'] = '0'
            
        return output
        
        
    def to_json(self):
        """
        Return a parsed dictionary that is JSON compatible.
        """
        return {
            'user': self.user,
            'code': self.code,
            'created': udatetime.to_string(self.created),
            'expires_at': udatetime.to_string(self.expires_at()),
            'expires': self.expires,
            'used': self.used
        }

def CodeManager:
    index = "index:code:by-date"
    
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        """
        redis_url, string: connection info for redis.
        """
        self.redis = redis.StrictRedis.from_url(redis_url, decode_responses=True, encoding='utf-8')
        self.users = user.manager.UserManager(redis_url=redis_url)
        
    def cleanup(self, id):
        """
        Remove the code and clean up any indices. Called after self.post(),
        possibly called asynchronously via a message queue.
        """
        self.delete(id)
        
    def post(self, id):
        """
        Called after the code is used. This is where you'd activate a user,
        or reset a password.
        """
        self.cleanup(id)
        
    def new(self, username):
        """
        Create a new code. 
        """
        user = self.users.get(username)
        
        code = Code(user=user.id)
        
        with self.redis.pipeline() as pipe:
            pipe.hmset(code.key, code.to_redis())
            pipe.expire(code.key, code.expires)
            pipe.lpush(self.index, code.code)
            pipe.execute()
            
        return code
        
    def get(self, id):
        """
        Retrieve an existing code.
        """
        key = Code.prefix(id)
        
        with self.redis.pipeline() as pipe:
            pipe.hgetall(key)
            pipe.ttl(key)
            results = pipe.execute()
        
        if not results[0]:
            raise errors.CodeNotFound()
            
        data = results[0]
        data['expires'] = results[1]
        
        code = Code.from_redis(data)
        
        return code
        
    def delete(self, id):
        """
        Remove an existing code.
        """
        key = Code.prefix(code)
        
        if not self.exists(code):
            raise errors.CodeNotFound()
        
        with self.redis.pipeline() as pipe:
            pipe.delete(key)
            pipe.lrem(self.index, 0, id)
            pipe.execute()
        
    def use(self, id, username, password=None):):
        """
        Use the given code. Verify the user's password if desired.
        """
        user = self.users.get(username)
        
        if password is not None:
            if not user.authenticate(password):
                raise errors.FailedAuthentication()
                
        code = self.get(id)
        
        if code.used:
            raise errors.CodeAlreadyUsed()
        
        if code.user != user.id:
            raise errors.UserMismatch()
        
        with self.redis.pipeline() as pipe:
            pipe.hmset(code.key, {'used': '1'})
            pipe.execute()
        
        self.post(id)
        
    def count(self):
        """
        Return the total number of codes in the system.
        """
        return self.redis.llen(self.index)
        
    def codes(self, start=0, stop=-1):
        """
        Return a list of Code objects. Paginate using start and stop.
        """
        codes = self.redis.lrange(self.index, start, stop)
        
        output = []
        
        with self.redis.pipeline() as pipe:
            for id in codes:
                key = Code.prefix(id)
                pipe.hgetall(key)
                pipe.ttl(key)
                
            results = pipe.execute()
            
            for data, ttl in util.grouper(results, 2):
                if data:
                    data['expires'] = ttl
                    output.append(Code.from_redis(data))
                else:
                    output.append(None)
                
        return output