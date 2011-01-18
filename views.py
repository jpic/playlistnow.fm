from django.core import urlresolvers
from django import http
from django import shortcuts
from django import template
from django.db.models import get_model
from django.contrib.auth import decorators
from django.contrib.auth.models import User

from tagging.models import Tag, TaggedItem
from actstream.models import actor_stream, user_stream, model_stream
from actstream import action

from playlist.models import Playlist
from music.models import Track

from forms import PostRegistrationForm

def add_activity(request):
    if not request.method == 'POST':
        return http.HttpResponseForbidden()

    if 'action_object_pk' in request.POST.keys():
        action_object = shortcuts.get_object_or_404(
            get_model(
                request.POST['action_object_app'],
                request.POST['action_object_class']
            ),
            pk=request.POST['action_object_pk']
        )
    else:
        action_object = None
    
    if 'action_object_pk' in request.POST.keys():
        action_object = shortcuts.get_object_or_404(
            get_model(
                request.POST['action_object_app'],
                request.POST['action_object_class']
            ),
            pk=request.POST['action_object_pk']
        )
    else:
        action_object = None

    action.send(
        request.user,
        request.POST['verb'],
        action_object=action_object,
        target=action_object
    )

    return http.HttpResponse('success')

def user_details(request, slug, tab='activities',
    template_name='auth/user_detail.html', extra_context=None):
    context = {
        'tab': tab,
    }

    user = shortcuts.get_object_or_404(User, username=slug)
    context['user'] = user

    if tab == 'playlists':
        context['playlists'] = user.playlist_set.all()
    elif tab == 'activities':
        activities = actor_stream(user)
        previous = None
        for activity in activities:
            if hasattr(activity, 'action_object'):
                if hasattr(previous, 'action_object') and previous.action_object.__class__ == activity.action_object.__class__ and activity.verb == previous.verb:
                    activity.action_object_group = previous.action_object_group
                else:
                    activity.action_object_group = [activity.action_object]
                
            if previous and activity.verb == previous.verb:
                activity.open = False
                previous.close = False
                if hasattr(activity, 'action_object') and activity.action_object.__class__ == previous.action_object.__class__:
                    if activity.action_object not in activity.action_object_group:
                        activity.action_object_group.append(activity.action_object)
            else:
                activity.open = True
                if previous:
                    previous.close = True
            
            previous = activity
        activities[0].open = True
        activities[len(activities)-1].close = True
        context['activities'] = activities

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
