from django import http
from django import shortcuts
from django import template
from django.contrib.auth import decorators

from tagging.models import Tag, TaggedItem
from django.contrib.auth.models import User

from playlist.models import Playlist

def user_details(request, slug,
    template_name='auth/user_detail.html', extra_context=None):
    context = {}

    context['object'] = shortcuts.get_object_or_404(User, username=slug)
    context['object_list'] = context['object'].playlist_set.all()

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def tag_details(request, slug,
    template_name='tagging/tag_detail.html', extra_context=None):
    context = {}

    context['object'] = shortcuts.get_object_or_404(Tag, name=slug)
    context['object_list'] = TaggedItem.objects.get_by_model(
        Playlist, context['object'])

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def empty(request,
    template_name='site_base.html', extra_context=None):
    context = {
        'empty': True,
    }

    if request.user.is_authenticated():
        context['my_playlists'] = Playlist.objects.filter(creation_user=request.user)[:20]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
