import re

from django import http
from django.conf import settings

JS_AGENTS = [
    'gecko',
    'msie',
]
IGNORE = r'^(site_media)|(ajax)'

class DynamicHtmlMiddleware(object):
    def process_request(self, request):
        if request.path == '/empty/' or request.is_ajax() or request.path.find('site_media') > 0 or request.path.find('admin') > 0:
            return None
        
        test = request.META['HTTP_USER_AGENT'].lower()
        for agent in JS_AGENTS:
            if test.find(agent) > 0:
                return http.HttpResponseRedirect('/empty/#' + request.path)
