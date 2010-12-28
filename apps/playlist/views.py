from django import http
from django import shortcuts
from django import template
from django.contrib.auth import decorators
from django.db.models import Q

from models import *
from forms import *

def playlist_category_details(request, slug,
    template_name='playlist/category_details.html', extra_context=None):
    context = {}

    context['object'] = shortcuts.get_object_or_404(PlaylistCategory, slug=slug)

    context['object_list'] = Playlist.objects.filter(
        Q(category__slug=slug) |
        Q(category__parent__slug=slug)
    ).select_related()

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def playlist_list(request, qs=Playlist.objects.all(),
    template_name='playlist/playlist_list.html', extra_context=None):
    context = {}
    
    context['object_list'] = qs

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

@decorators.login_required
def playlist_add(request, form_class=PlaylistAddForm,
    template_name='playlist/playlist_add.html', extra_context=None):
    context = {}

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            object = form.save(commit=False)
            object.creation_user = request.user
            object.save()
            return http.HttpResponseRedirect(object.get_absolute_url())
    else:
        form = form_class()
    
    context['form'] = form

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def playlist_details(request, user, slug,
    template_name='playlist/playlist_details.html', extra_context=None):
    context = {}

    object = shortcuts.get_object_or_404(Playlist, creation_user__username=user,slug=slug)
    context['object'] = object

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
