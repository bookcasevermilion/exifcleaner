"""
Base class for Manager objects.
"""

import redis
import os

class BaseManager:
    """
    Collection of common functionality across manager classes.
    """
    def __init__(self, redis_url="redis://127.0.0.1:6379"):
        """
        redis_url, string: connection info for redis. Can be overridden with the
        EXIFCLEANER_REDIS_URL variable.
        """
        from_environ = os.environ.get("EXIFCLEANER_REDIS_URL", None)
        
        if from_environ is not None:
            redis_url = from_environ
        
        self.redis_url = redis_url
        
        self.redis = redis.StrictRedis.from_url(redis_url, decode_responses=True, encoding='utf-8')