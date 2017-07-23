from webob import Request, Response
from . import util
import pprint
import piexif
import tempfile
import os
import redis
from rq import Queue
import englids
import json

class ExifImage:
    """
    Wrapper for some common exif tag manipulations
    """
    
    def __init__(self, path):
        self.path = path
        self._exif = {}
        
    @property
    def exif(self):
        self.read()
        
        return self._exif
        
    def read(self, force=False):
        """
        Read/re-read the exif data of the image.
        """
        if not self._exif or force:
            self._exif = piexif.load(self.path)
        
    def dump(self):
        """
        Create a JSON file containing the exif data (minus the thumbnail)
        """
        exif = self.exif.copy()
        del exif['thumbnail']
        
        path = self._json_path()
        
        with open(path) as fp:
            json.dump(exif, fp)
        
    def _json_path(self):
        """
        Create a json path for the image. (e.g. file.json)
        """
        name, suffix = os.path.splitext(self.path)
        
        return "{}.json".format(name)
            
        
    def _thumb_path(self):
        """
        Create a thumbnail path for the image. Uses the image name, and puts ".thumb" between
        the name and suffix (e.g. file.thumb.jpg)
        """
        name, suffix = os.path.splitext(self.path)
        
        return "{}.thumb{}".format(name, suffix)
        
        
    def thumb(self):
        """
        Extract the thumbnail from the exif data. Returns False if there is none,
        the new path name if successfully extracted.
        """
        if "thumbnail" in self.exif:
            with open(self._thumb_path(), "wb") as fp:
                fp.write(self.exif['thumbnail'])
                
            return self._thumb_path()
        else:
            return False
        
    @property
    def orientation(self):
        # exif['0th'][274] == orientation.
        flag = self.exif.get('0th', {}).get(274, 1)
        
        return flag
        
    @property
    def rotated(self):
        """
        Returns True if the image has exif data that sets the orientation.
        """
        # if the orientation flag is 1, the image isn't rotated.
        if self.orientation > 1:
            return True
        else:
            return False
        
    def save(self):
        """
        Write the exif data as it stands into the file.
        """
        piexif.insert(piexif.dump(self.exif), self.path)
        
    def clean(self):
        """
        Remove the exif tags from the image, but preserve
        the original orientation flag.
        """
        if self.rotated:
            # preserve initial rotation
            old_rotation = self.orientation
        
            piexif.remove(self.path)
        
            self.read(force=True)
        
            self._exif['0th'][274] = old_rotation
            
            self.save()
        else:
            piexif.remove(self.path)
        
def temppath(id_, tempdir="./tmp"):
    filename = "{}.jpg".format(id_)
    path = os.path.join(tempdir, filename)
    
    return path
        
def tempexif(source, id_, tempdir="./tmp"):
    """
    Factory - saves the bytes in fp into a temporary location,
    returns an ExifImage object.
    """
    path = temppath(id_, tempdir)
    
    with open(path, 'wb') as fp:
        while True:
            data = source.read(8192)
            if not data:
                break
            
            fp.write(data)
            
    return ExifImage(path)

def process(id_, temp_dir):
    path = temppath(id_, temp_dir)
    exif = ExifImage(path)
    
    exif.thumb()
    exif.dump()
    exif.clean()

def dump_json(id_, temp_dir):
    path = temppath(id_, temp_dir)
    exif = ExifImage(path)
    exif.dump()

def extract_thumbnail(id_, temp_dir):
    path = temppath(id_, temp_dir)
    exif = ExifImage(path)
    exif.thumb()
    
def clean_exif_data(id_, temp_dir):
    path = temppath(id_, temp_dir)
    exif = ExifImage(path)
    
    exif.clean()

def enqueue(queue, id_, connection):
    """
    Adds jobs to the queue:
    
    1. Extract the thumbnail if present.
    2. Rotate if necessary.
    3. Clean out exif data.
    
    Returns a list of job objects.
    """


class ExifCleanerService:
    """
    Provides a RESTful web service that takes an image, extracts its exif data,
    and returns a summary of what was extracted, along with a link to a new copy
    of the image with the exif data removed.
     
    Path             Type             Mime                Request Contains
    ---------------- ---------------- ------------------- ----------------------         
    /clean           POST             binary data;        JSON; exif data and temporary link to cleaned file
    """
    
    def __init__(self, temp_dir="./tmp", redis_url="redis://localhost:6379/0", queue_name="exifcleaner"):
        self.redis = redis.StrictRedis.from_url(redis_url)
        self.queue_name = queue_name
        self.queue = Queue(self.queue_name, connection=self.redis)
        self.temp_dir = os.path.abspath(temp_dir)
        
        self.id_generator = englids.Englids()
    
    def __call__(self, environ, start_response):
        request = Request(environ)
        
        response = None
        
        parts = request.path.split("/")[1:]
        
        print(parts)
        
        try:
            if parts[0] == 'clean':
                response = self.clean(request)
            elif parts[0] == 'status':
                if len(parts) != 2:
                    raise util.BadRequest()
                else:
                    response = self.status(request, parts[1])
            else:
                raise util.NotFound()
        except util.BadRequest as e:
            return e(environ, start_response)
        
        return response(environ, start_response)
        
    def info(self, request):
        """
        Return a json serialized string with all of the exif data
        """
        response = Response()
        
        data = piexif.load(request.POST['input'].file.read())
        
        response.content_type = "text/plain"
        response.text = pprint.pformat(data)
        
        return response
    
    def status(self, request, id_):
        job = self.queue.fetch_job(id_)
        
        import pdb; pdb.set_trace();
        
        response = Response()
        
        response.json_body = job
        
        return response
        
    def clean(self, request):
        source = request.POST['input'].file
        id_ = self.id_generator()
        
        exif = tempexif(source, id_, self.temp_dir)
        
        job = self.queue.enqueue(process, id_=id_, temp_dir=self.temp_dir, job_id=id_)
        
        response = Response()
        response.content_type = "application/javascript"
        
        response.text = id_
        
        return response
        
    def dump_request(self, request):
        response = Response()
        response.content_type = "text/plain"
        response.text = pprint.pformat(request.environ)
        response.text += "\n\n------------------\n\n"
        response.text += pprint.pformat(dir(request))
        
        return response

