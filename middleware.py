import re

from django import http
from django.conf import settings
from django.core import urlresolvers

JS_AGENTS = [
    'gecko',
    'msie',
    'vimprobable',
    'vimpression',
]
IGNORE = r'^(site_media)|(ajax)'

class DynamicHtmlMiddleware(object):
    def process_request(self, request):
        if not getattr(settings, 'AJAX_NAVIGATION', False):
            request.noreload = True
            return None

        # attempt to fix winetricks ie7
        #offset = request.path_info.find('#')
        #if offset:
            #request.path_info = request.path_info[0:offset]

        #offset = request.path.find('#')
        #if offset:
            #request.path = request.path[0:offset]
        
        request.modal = request.GET.get('modal', False)

        for url in settings.UI_IGNORE_URLS:
            if url in request.path_info:
                request.noreload = True
                request.ajax = False
                return None

        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            # probably from javascript
            request.ajax = True
        
        elif request.path == '/empty/':
            # this response should be the ajax container
            request.ajax = False

        elif request.GET.get('ajax', False):
           # local redirects to ajax (see process_response())
           request.ajax = True

        elif request.path != '/empty/' and request.method != 'POST':
            # automatic redirect to container for chrome user agents
            print request.META
            test = request.META['HTTP_USER_AGENT'].lower()
            for agent in JS_AGENTS:
                if test.find(agent) > -1:
                    return http.HttpResponseRedirect('/empty/#' + request.path)

    def process_response(self, request, response):
        for url in settings.UI_IGNORE_URLS:
            if url in request.path_info:
                return response

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
