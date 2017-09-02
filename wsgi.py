from exifcleaner import ExifCleanerService
from webob.static import DirectoryApp
import re

static = DirectoryApp("./static")
data = DirectoryApp("./tmp")

cleaner = ExifCleanerService()

def app(environ, start_response):
    print("FIRST", environ['PATH_INFO'])
    if re.search("/(clean)|(status/[^/]+)|(cancel/[^/]+)$", environ['PATH_INFO']):
        return cleaner(environ, start_response)
    elif re.search("^/data", environ['PATH_INFO']):
        environ['PATH_INFO'] = environ['PATH_INFO'].replace("/data", "", 1)
        return data(environ, start_response)
    else:
        return static(environ, start_response)
