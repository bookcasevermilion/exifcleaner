"""
Helper functions and such for tests.
"""

import redis
import os

def check_redis():
    """
    Return True if redis is up and available.
    """
    redis_url = os.environ.get("EXIFCLEANER_REDIS_URL", "redis://127.0.0.1:6379")
    
    try:
        conn = redis.StrictRedis.from_url(redis_url)
        response = conn.ping()
        
        return response
        
    except redis.exceptions.ConnectionError:
        return False