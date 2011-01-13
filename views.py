from django.core import urlresolvers
from django import http
from django import shortcuts
from django import template
from django.contrib.auth import decorators

from tagging.models import Tag, TaggedItem
from django.contrib.auth.models import User

from playlist.models import Playlist

from forms import PostRegistrationForm

def user_details(request, slug, tab='activities',
    template_name='auth/user_detail.html', extra_context=None):
    context = {
        'tab': tab,
    }

    user = shortcuts.get_object_or_404(User, username=slug)
    context['user'] = user

    if tab == 'playlists':
        context['playlists'] = user.playlist_set.all()

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

def postregistration(request, form_class=PostRegistrationForm,
    template_name='postregistration.html', extra_context=None):
    context = {}

    if request.method == 'POST':
        form = form_class(request.POST, instance=request.user, request=request)
        if form.is_valid():
            form.save()
            return http.HttpResponseRedirect(urlresolvers.reverse('postlogin'))
    else:
        form = form_class(instance=request.user, request=request)
    
    context['form'] = form
    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def postlogin(request,
    template_name='postlogin.html', extra_context=None):
    context = {}

    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()
    
    if not request.user.first_name:
        return http.HttpResponseRedirect(urlresolvers.reverse('postregistration'))
    
    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
