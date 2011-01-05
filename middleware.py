import re

from django import http
from django.conf import settings

JS_AGENTS = [
    'gecko',
    'msie',
    'vimprobable',
    'vimpression',
]
IGNORE = r'^(site_media)|(ajax)'

class DynamicHtmlMiddleware(object):
    def process_request(self, request):
        request.modal = request.GET.get('modal', False)
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            # probably from javascript
            request.ajax = True
        
        elif request.path == '/empty/':
            # this response should be the ajax container
            request.ajax = False

        elif '/admin' in request.path:
            # isolate django.contrib.admin
            request.ajax = False
        
        elif '/site_media' in request.path:
            # isolate django-static
            request.ajax = False

        elif request.GET.get('ajax', False):
           # local redirects to ajax (see process_response())
           request.ajax = True

        else:
            # automatic redirect to container for chrome user agents
            test = request.META['HTTP_USER_AGENT'].lower()
            for agent in JS_AGENTS:
                if test.find(agent) > 0:
                    return http.HttpResponseRedirect('/empty/#' + request.path)

    def process_response(self, request, response):
        new_url = False

        location = response.get('Location', '')
        if location == '/account/login/':
            response['Location'] = response['Location'] + '?modal=1'

        if location and location[0] == '/':
            # internal redirect, forward ajax
            if location.find('/?') > -1:
                new_url = location.replace('/?', '/?ajax=1&')
            else:
                new_url = location + '?ajax=1'

            if new_url:
                response = http.HttpResponseRedirect(new_url)

        return response
