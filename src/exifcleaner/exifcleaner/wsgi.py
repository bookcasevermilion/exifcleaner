"""
WSGI Entry Point For Common Functionality.
"""

from webob import Request, Response
from . import util
from . import errors
from . import jobs
import pprint
import piexif
import tempfile
import os
import redis
from rq import Queue, get_current_job
from rq.connections import get_current_connection
from rq_scheduler import Scheduler
import englids
import json
import datetime
from datetime import timedelta
from .image import ExifImage, tempexif


class ExifCleanerService:
    """
    Provides a RESTful web service that takes an image, extracts its exif data,
    and returns a summary of what was extracted, along with a link to a new copy
    of the image with the exif data removed.
     
    Path             Type             Purpose              Mime                Response Contains
    ---------------- ---------------- -------------------- ------------------- ----------------------         
    /clean           POST             submit image for     application/json    id of the image
                                      processing
    /status/[id]     GET              processing status    application/json    dictiornay of status info
    /cancel/[id]     PUT              cancel processing    application/json    true
    """                              
    
    def _check_config(self, config):
        """
        Internal function, used to validate configuration passed to the constructor.
        """
        if not os.path.exists(config['data_dir']):
            raise errors.ExifCleanerError("Path '{}' does not exist".format(config['data_dir']))
        
        if config['ttl'] > config['id_lifespan']:
            raise errors.ExifCleanerError("TTL for images can not be longer than the lifespan of an id")
    
    def __init__(self, data_dir="./tmp", redis_url="redis://localhost:6379/0", queue_name="exifcleaner", ttl=600):
        """
        Configure the service.
        
        data_dir - string, path where files will be stored once they are uploaded.
        redis_url - string, connection details for the redis server.
        queue_name - string, name of the RQ queue
        ttl - integer, number of seconds to keep images around after they are processed.
        """
        config = {
            # location where files are stored
            'data_dir': os.path.abspath(data_dir),
            
            # url for connecting to the redis server
            'redis_url': redis_url,
            
            # a name for the RQ job queue
            'queue_name': queue_name,
            
            # the number of seconds an image will exist after its processed.
            'ttl': ttl,
            
            # how long to keep ids around before they expire, in seconds
            # default is ~ 1 year
            'id_lifespan': 31536000
        }
        
        self._check_config(config)
        
        self.config = config
        
        self.redis = redis.StrictRedis.from_url(redis_url)
        self.queue_name = queue_name
        self.queue = Queue(self.config['queue_name'], connection=self.redis)
        self.data_dir = self.config['data_dir']
        
        self.id_generator = englids.Englids()
    
    def __call__(self, environ, start_response):
        """
        Main - handles routing to other methods.
        """
        request = Request(environ)
        
        response = None
        
        parts = request.path.split("/")[1:]
        
        try:
            if parts[0] == 'clean':
                response = self.clean(request)
            elif parts[0] == 'status':
                if len(parts) != 2:
                    raise util.BadRequest()
                else:
                    response = self.status(request, parts[1])
            elif parts[0] == 'cancel':
                if request.method != 'PUT':
                    raise util.BadRequest()
                
                if len(parts) != 2:
                    raise util.BadRequest()
                else:
                    response = self.status(request, parts[1])
            else:
                raise util.NotFound()
        except util.BadRequest as e:
            return e(environ, start_response)
        
        return response(environ, start_response)
    
    def id(self):
        """
        Generate a random unique id. Checks the database to ensure it hasn't been
        used already.
        
        Logs the new id in the database. Ids expire after self.config['id_lifespan']
        seconds, using redis' EXPIRE mechanism.
        
        Retries 5 times. Raises TooManyRetriesError if the same id is generated 
        over and over.
        """
        
        id_ = self.id_generator()
        
        max_tries = 5
        tries = 0
        
        while tries < max_tries:
            exists = self.redis.exists("exif:{}".format(id_))
            if not exists:
                break
            else:
                id_ = self.id_generator()
                
            tries += 1
        else:
            raise errors.ExifCleanerTooManyRetries()
        
        key = "exif:{}".format(id_)
        with self.redis.pipeline() as pipe:
            pipe.set(key, 1)
            pipe.expire(key, self.config['id_lifespan'])
            pipe.execute()
            
        return id_
    
    def cancel(self, request, id_):
        """
        Cancel a job for the given image id.
        """
        job = self.queue.fetch_job(id_)
        
        response = Response()
        
        response.json_body = "true"
        
        job.cancel()
        
        return response
        
    
    def status(self, request, id_):
        """
        Return a json string with status info.
        
        Data is just proxied from the RQ job
        """
        job = self.queue.fetch_job(id_)
        
        response = Response()
        
        response.json_body = {
            'ttl': job.ttl,
            'status': job.status,
            "is_failed": job.is_failed,
            "is_finished": job.is_finished,
            "is_queued": job.is_queued,
            "is_started": job.is_started,
            "timeout": job.timeout,
            "result": job.result
        }
        
        return response
        
    def clean(self, request):
        """
        Submit a file to be cleaned. Only supports JPEG images.
        """
        source = request.POST['input'].file
        id_ = self.id()
        
        try:
            exif = tempexif(source, id_, self.data_dir)
        except errors.ExifCleanerNotAJPEG:
            raise util.BadRequest("File is not a JPEG")
        
        job = self.queue.enqueue(jobs.process, id_=id_, data_dir=self.data_dir, job_id=id_)
        
        response = Response()
        response.json_body = id_
        
        return response

