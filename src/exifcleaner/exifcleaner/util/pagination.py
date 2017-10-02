"""
Pagination helpers.
"""

from webob import Request, Response
from wsgiref.util import request_uri, guess_scheme, application_uri
from urllib.parse import urljoin, urlparse, urlunparse, urlencode
from . import web

import simpleschema

schema = simpleschema.Schema({
    'per-page': simpleschema.fields.IntegerField(default=20, min=0, max=100),
    'page': simpleschema.fields.IntegerField(default=1, min=0)
})

def link(base, page, per_page):
    url_parts = list(urlparse(base))
    
    query = {'page':page}
    
    if schema['per-page'].default != per_page:
        query['per-page'] = per_page
        
    url_parts[4] = urlencode(query)
    
    return urlunparse(url_parts)

def nav(request, count):
    """
    Given a WebOb request object, and data about the information being
    paged through, return a structure representing the navigation:
    
    >>> nav(req, 30)
    {'next': http://url/page=3&per-page=30,
     'previous': http://url/page=2&per-page=30,
     'count': count,
     'start': 20,
     'end': 39}
     
    In the event of a malformed input, JSONError is raised with the
    proper error codes.
    """
    errors = []
    
    output = {
        'count': count
    }
    
    for field, result in schema.validate(request.GET.mixed()):
        if field == 'per-page': 
            if isinstance(result, Exception):
                errors.append(1202)
        if field == 'page':
            if isinstance(result, Exception):
                errors.append(1201)
                
        output[field] = result
    
    if errors:
        raise web.JSONError(errors)
    
    per_page = output['per-page']
    page = output['page']
    
    start = (page*per_page) - per_page
    end = (page*per_page) - 1
    
    next = page + 1
    previous = page - 1
    
    if end > count:
        next = None
    
    if page == 1:
        previous = None
    
    uri = request_uri(request.environ)
    
    if previous is not None:
        output['previous'] = link(uri, previous, per_page)
        
    if next is not None:
        output['next'] = link(uri, next, per_page)
        
    output['start'] = start
    output['end'] = end
        
    return output
    