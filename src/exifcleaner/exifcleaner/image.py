"""
Classes/functions for working with images.
"""

import json
import piexif
import tempfile
import shutil
import os
from . import errors
from . import util

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
        
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(exif, fp, cls=util.ExifJSONEncoder)
            
        return self.json_name
        
    @property
    def name(self):
        """
        Return the name of the file, for downloading later.
        """
        return os.path.basename(self.path)
        
    @property
    def json_name(self):
        """
        Create a json filename to be served later
        """
        name, suffix = os.path.splitext(self.name)
        
        return "{}.json".format(name)
        
    @property
    def thumb_name(self):
        """
        Create a json filename to be served later
        """
        name, suffix = os.path.splitext(self.name)
        
        return "{}.thumb{}".format(name, suffix)
        
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

def tempexif(source, id_, dest):
    """
    Factory - saves the bytes in fp into a temporary location, copies 
    it to the final destination.
    
    Returns an ExifImage object.
    """
    path = os.path.join(dest, "{}.jpg".format(id_))
    
    with tempfile.NamedTemporaryFile() as fp:
        # check the first two bytes
        magic_number = source.read(2)
        if magic_number != b"\xff\xd8":
            raise errors.ExifCleanerNotAJPEG()
        
        fp.write(magic_number)
        
        while True:
            data = source.read(8192)
            if not data:
                break
            
            fp.write(data)
        
        shutil.copyfile(fp.name, path)
        
        fp.close()
    
            
    return ExifImage(path)