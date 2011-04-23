import re
import hotshot

from django import http
from django.conf import settings
from django.core import urlresolvers
from django.template import defaultfilters

JS_AGENTS = [
    'gecko',
    'msie',
    'vimprobable',
    'vimpression',
    'opera',
    'webkit',
]
BOTS = [
    'googlebot',
]
IGNORE = r'^(site_media)|(ajax)'

class OldUrlsMiddleware(object):
    def process_response(self, request, response):
        if response.status_code != 404:
            return response
        path = request.META.get('PATH_INFO', '/')

        m = re.match(r'.*/song/(?P<artist>[^/]*)/(?P<track>[^/]*)/?$', path)
        if m is not None:
            return http.HttpResponseRedirect(urlresolvers.reverse('music_track_details', args=(
                defaultfilters.slugify(m.group('artist').replace('+', ' ')),
                defaultfilters.slugify(m.group('track').replace('+', ' ')),
            )))

        return http.HttpResponse(status=401)

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
            #print "testing %s against %s" % (url, request.path_info)
            if url in request.path_info:
                #print "CONTINUE NORMAL"
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
            test = request.META.get('HTTP_USER_AGENT', '').lower()
            #for bot in BOTS:
                #if test.find(agent) > -1:
                    #return None
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

        if request.path_info == '/account/logout/':
            response['Location'] = '/'

        if location and location[0] == '/':
            # internal redirect, forward ajax
            if location.find('/?') > -1:
                new_url = location.replace('/?', '/?ajax=1&')
            else:
                new_url = location + '?ajax=1'

            if new_url:
                response = http.HttpResponseRedirect(new_url)

        return response

    #def process_view(self, request, view_func, view_args, view_kwargs):
        
        #profiler = hotshot.Profile('/tmp/django.prof')
        #response = profiler.runcall(view_func, request, *view_args, **view_kwargs)
        #profiler.close()
        
        ## process results
        
        #return response

