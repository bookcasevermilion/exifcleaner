from exifcleaner import ExifCleanerService
from webob.static import DirectoryApp
import re

static = DirectoryApp("./static")

cleaner = ExifCleanerService()

def app(environ, start_response):
    print(environ['PATH_INFO'])
    if re.search("/(clean)|(status/[^/]+)$", environ['PATH_INFO']):
        return cleaner(environ, start_response)
    else:
        return static(environ, start_response)
