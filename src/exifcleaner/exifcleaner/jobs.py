"""
Job functions.
"""

from .image import ExifImage
import os
from rq import Queue, get_current_job
from rq.connections import get_current_connection
from rq_scheduler import Scheduler
from . import errors
from . import util
import datetime

def cleanup(id_, data_dir):
    """
    Remove files.
    
    id_ - the job to clean up after
    data_dir - where files live
    """
    print("Deleting for {}".format(id_))
    
    img = os.path.join(data_dir, "{}.jpg".format(id_))
    thumb = os.path.join(data_dir, "{}.thumb.jpg".format(id_))
    json = os.path.join(data_dir, "{}.json".format(id_))
    
    for path in [img, thumb, json]:
        if os.path.exists(path):
            print("Removing {}".format(path))
            os.remove(path)
        else:
            print("File {} doesn't exist".format(path))
    

def process(id_, data_dir, clean_in=10):
    """
    Job to remove the exif data from an uploaded image.
    
    The exif data is saved as a json file.
    
    If the image had an exif thumbnail, it is saved as a separate file.
    """
    path = os.path.join(data_dir, "{}.jpg".format(id_))
    exif = ExifImage(path)
    
    exif.thumb()
    exif.dump()
    exif.clean()
    
    job = get_current_job()
    
    # schedule the cleanup task
    now = datetime.datetime.now()
    scheduler = Scheduler(queue_name=job.origin, connection=get_current_connection())
    scheduler.enqueue_in(datetime.timedelta(minutes=clean_in), cleanup, id_, data_dir)
    
    removed_by = now+datetime.timedelta(minutes=clean_in)
    
    print("Added at: {}".format(now.isoformat()))
    print("Removed by: {}".format(removed_by.isoformat()))
    
    return {
        'thumb': exif.thumb_name,
        'json': exif.json_name,
        'removed_around': removed_by.isoformat()
    }
