import lastfm

from django import http
from django import shortcuts
from django import template
from django.contrib.auth import decorators
from django.conf import settings

from models import *
#from forms import *

def get_lastfm_api():
    return lastfm.Api(settings.LASTFM_API_KEY)

def music_search(request, qname='term',
    template_name='music/search.html', extra_context=None):
    context = {}

    if qname in request.GET.keys():
        q = request.GET[qname]

        try:
            api = get_lastfm_api()
            artists = api.search_artist(q)
            
            context['artists'] = []
            for artist in artists:
                if not artist.streamable:
                    continue
                context['artists'].append(artist)
        except lastfm.LastfmError:
            pass

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
