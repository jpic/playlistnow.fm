from django import http
from django import shortcuts
from django import template
from django.contrib.auth import decorators

from models import *
#from forms import *

def music_search(request,
    template_name='music/search.html', extra_context=None):
    context = {}

    

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
