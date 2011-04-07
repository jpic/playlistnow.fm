from operator import or_
from datetime import date, timedelta

from django.conf import settings
from django.core.cache import cache
from django.core import urlresolvers
from django import http
from django import shortcuts
from django import template
from django.db.models import get_model, Q
from django.db import connection, transaction
from django.contrib.auth import decorators
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote
from django.contrib import messages

from notification.models import Notice
from tagging.models import Tag, TaggedItem
from actstream.models import actor_stream, user_stream, model_stream, Follow, Action
from actstream import action
from endless_pagination.decorators import page_template

from music.views import return_json
from playlist.models import *
from music.models import Track, Recommendation
from forms import *

def make_cache_key(fragment_name, *variables):
    args = md5_constructor(u':'.join([urlquote(var) for var in variables]))
    cache_key = '%s.%s' % (fragment_name, args.hexdigest())
    return cache_key

def invalidate_cache_key(fragment_name, *variables):
    args = md5_constructor(u':'.join([urlquote(var) for var in variables]))
    cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
    cache.delete(cache_key)

def group_activities(activities):
    if not activities:
        return activities

    previous = None
    group = []
    groups = []
    group_verbs = ('liked track', 'added track to playlist', 'becomes fan of artist')
    for activity in activities:
        if previous and activity.verb == previous.verb and activity.verb in group_verbs and activity.actor == previous.actor:
            if activity.verb == 'added track to playlist' and activity.target != previous.target:
                do_group = False
            else:
                do_group = True
        else:
            do_group = False

        if do_group:
            # this activity groups with the previous one
            group.append(activity)
        else:
            # this activity does not group with the previous one
            # save the previous group if there is a previous one
            if previous:
                groups.append(group)
            # create a new group
            group = [activity]

        # the activity may need to know its own group
        activity.group = group

        # this activity is the "previous" one of the next loop
        previous = activity

    # if the last activity groupped then it would not have been appended to groups
    if len(groups) < 1 or groups[-1] is not group:
        groups.append(group)

    # second pass, adding properties to activities, required to display
    for group in groups:
        # the first of each group opens the activity line
        group[0].open = True
        # the last of each group closes the activity line
        group[-1].close = True
        if getattr(group[0], 'action_object', False):
            # action objects must be grouped in their own list for render_tracks and such
            action_object_group = [a.action_object for a in group]
            # and given to the closer
            group[-1].action_object_group = action_object_group
        # the earliest activity of the group is the one to comment
        earliest = None
        for activity in group:
            if earliest is None:
                earliest = activity
            elif earliest.pk > activity.pk:
                earliest = activity
        for activity in group:
            activity.earliest_of_group = earliest

    activities[0].open = True
    activities[len(activities)-1].close = True
    return activities

@decorators.login_required
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

@decorators.login_required
def action_like(request, action_id):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()
    try:
        object = Action.objects.get(pk=action_id)
    except Action.DoesNotExist:
        return http.HttpResponseNotFound('could not find action with id %s' % action_id)
    request.user.playlistprofile.fanof_actions.add(object)
    #action.send(request.user, verb='likes', action_object=object)
    return http.HttpResponse('action liked')

@decorators.login_required
def action_unlike(request, action_id):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()
    try:
        action = Action.objects.get(pk=action_id)
    except Action.DoesNotExist:
        return http.HttpResponseNotFound('could not find action with id %s' % action_id)
    request.user.playlistprofile.fanof_actions.remove(action)
    return http.HttpResponse('action unliked')

@decorators.login_required
def action_delete(request, action_id):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()
    try:
        action = Action.objects.get(pk=action_id)
    except Action.DoesNotExist:
        return http.HttpResponseNotFound('could not find action with id %s' % action_id)
    if action.actor != request.user:
        return http.HttpResponseForbidden('you may only delete your own actions')
    action.delete()
    return http.HttpResponse('action deleted')

def user_search_autocomplete(request, qname='query', qs=User.objects.all()):
    if not request.GET.get(qname, False):
        return return_json()

    q = request.GET[qname]

    response = {
        'query': request.GET[qname].encode('utf-8'),
        'suggestions': [],
        'data': [],
    }

    qs = qs.filter(
        Q(username__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q)
    ).select_related('playlistprofile').distinct()

    for user in qs[:15]:
        response['suggestions'].append(unicode(user.playlistprofile))
        response['data'].append({
            'url': user.playlistprofile.get_absolute_url(),
            'html': '<img src="%s"> %s' % (
                user.playlistprofile.avatar_url,
                unicode(user.playlistprofile),
            )
        })

    return return_json(response)

def friends_search_autocomplete(request, qname='query'):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    if not request.GET.get(qname, False):
        return return_json()

    q = request.GET[qname]
    qs = request.user.playlistprofile.friends()
    qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q))
    qs = qs.distinct('pk')
    print qs

    response = {
        'query': request.GET[qname].encode('utf-8'),
        'suggestions': [],
        'data': [],
    }

    for user in qs:
        response['suggestions'].append(unicode(user.playlistprofile))
        response['data'].append({
            'url': user.playlistprofile.get_absolute_url(),
            'html': '<img src="%s"> %s' % (
                user.playlistprofile.avatar_url,
                unicode(user.playlistprofile),
            ),
            'pk': user.pk,
        })

    return return_json(response)

def user_search(request, qname='term', qs=User.objects.all(),
    template_name='auth/user_list.html', extra_context=None):
    context = {}
    q = request.GET.get(qname, '')
    qs = qs.filter(
        Q(username__icontains=q) |
        Q(first_name__icontains=q) |
        Q(last_name__icontains=q)
    ).select_related('playlistprofile')
    context['object_list'] = qs
    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

@page_template('auth/user_activities.html')
def user_details(request, slug, tab='activities',
    template_name='auth/user_detail.html', extra_context=None):
    context = {
        'tab': tab,
    }
    
    if 'page' not in request.GET or tab != 'activities':
        template_name = 'auth/user_detail.html'

    user = shortcuts.get_object_or_404(User, username=slug)
    context['user'] = user

    c = ContentType.objects.get_for_model(User)

    follows_users_ids = Follow.objects.filter(user=user,
                                              content_type__app_label='auth',
                                              content_type__model='user') \
                                      .exclude(object_id=user.pk) \
                                      .values_list('object_id', flat=True)
    follows_qs = User.objects.filter(id__in=follows_users_ids) \
                             .select_related('playlistprofile')
    followers_qs = User.objects.filter(follow__object_id=user.pk, follow__content_type=c).select_related('playlistprofile')

    context['follows'] = follows_qs
    if request.user.is_authenticated():
        context['do_i_follow'] = followers_qs.filter(pk=request.user.pk).count()
    else:
        context['do_i_follow'] = False

    if tab == 'playlists':
        context['playlists'] = user.playlist_set.all()
    elif tab == 'activities':
        activities = Action.objects.filter(
            Q(pk__in=actor_stream(user).values_list('pk')) |
            Q(
                action_object_content_type = ContentType.objects.get_for_model(Recommendation),
                action_object_object_id__in = Recommendation.objects.filter(target=user).values_list('id')
            ) | 
            Q(
                target_content_type = ContentType.objects.get_for_model(User),
                target_object_id = user.pk
            )
        ).order_by('-timestamp')
        context['activities'] = activities
    
    # for the sidebar
    context['follows_qs'] = follows_qs
    context['followers_qs'] = followers_qs
    context['follows'] = follows_qs._clone()[:20]
    context['followers'] = followers_qs._clone()[:20]

    profiles = user.twitterprofile_set.all()
    if profiles:
        context['twitterprofile'] = profiles[0]
    profiles = user.facebookprofile_set.all()
    if profiles:
        context['facebookprofile'] = profiles[0]
    profiles = user.gfcprofile_set.all()
    if profiles:
        context['gfcprofile'] = profiles[0]

    context['ctype'] = c
    context.update(extra_context or {})

    if tab != 'activities':
        del context['page_template']

    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def tag_details(request, slug,
    template_name='tagging/tag_detail.html', extra_context=None):
    context = {}

    context['object'] = shortcuts.get_object_or_404(Tag, name=slug)
    context['object_list'] = TaggedItem.objects.get_by_model(
        Playlist, context['object']).order_by('-tracks_count')

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
        context['notices'] = Notice.objects.notices_for(request.user, unseen=True)

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def home(request,
    template_name='homepage.html', extra_context=None):
    context = {}
    
    context['last_users'] = cache.get('last_users')
    if context['last_users'] is None:
        c = ContentType.objects.get_for_model(User)
        pks = Action.objects.filter(actor_content_type=c).order_by('-timestamp').values_list('actor_object_id', flat=True)
        final_pks = []
        for pk in pks:
            if len(final_pks) == 8:
                break
            if not pk in final_pks:
                final_pks.append(pk)
        context['last_users'] = User.objects.filter(pk__in=
            final_pks).distinct().select_related('playlistprofile')
        cache.set('last_users', list(context['last_users']), 3600*12)

    context['last_artists'] = cache.get('last_artists')
    if context['last_artists'] is None:
        context['last_artists'] = Artist.objects.filter(last_fan_datetime__isnull=False).order_by('-last_fan_datetime')[:8]
        cache.set('last_artists', list(context['last_artists']), 3600*12)

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

@decorators.login_required
@page_template('auth/user_activities.html')
def me(request,
    template_name='me.html', extra_context=None):
    context = {}

    if not request.user.is_authenticated():
        if not 'socialregistration_profile' in request.session:
            return http.HttpResponseRedirect(urlresolvers.reverse(
                'acct_signup'))
        elif not 'socialregistration_userdata' in request.session:
            return http.HttpResponseRedirect(urlresolvers.reverse(
                'socialregistration_userdata'))
        elif not 'socialregistration_friends' in request.session:
            return http.HttpResponseRedirect(urlresolvers.reverse(
                'socialregistration_friends'))
        else:
            return http.HttpResponseRedirect(urlresolvers.reverse(
                'socialregistration_complete'))
    
    user = request.user
    activities = Action.objects.filter(
        Q(pk__in=user_stream(user).values_list('pk')) |
        Q(pk__in=actor_stream(user).values_list('pk')) |
        Q(
            action_object_content_type = ContentType.objects.get_for_model(Recommendation),
            action_object_object_id__in = Recommendation.objects.filter(target=user).values_list('id')
        ) | 
        Q(
            target_content_type = ContentType.objects.get_for_model(User),
            target_object_id = user.pk
        )
    ).order_by('-timestamp')
    context['activities'] = activities

    context['who_to_follow'] = suggested_users_for(user)
    context['ctype'] = ContentType.objects.get_for_model(User)

    context['hot_tracks'] = []
    like_qs = Action.objects.filter(timestamp__gte=date.today() - timedelta(1))
    like_qs = like_qs.filter(verb='liked track')
    like_qs = like_qs.exclude(action_object_object_id__in=user.playlistprofile.tiny_playlist.tracks.all().values_list('pk'))
    like_friends_qs = like_qs.filter(actor_object_id__in=user.playlistprofile.friends().values_list('pk'))
    
    def get_sorted_tracks_from_actions(actions):
        points = {}
        for pk in actions.values_list('action_object_object_id', flat=True):
            if pk not in points.keys():
                points[pk] = 0
            points[pk] += 1

        sorted_points = sorted(points.iteritems(), key=operator.itemgetter(1))
        sorted_points.reverse()
        sorted_pks = [pk for pk, points in sorted_points][:8]
        tracks = Track.objects.filter(pk__in=sorted_pks)
        sorted_tracks = sorted(tracks, key=lambda track: sorted_pks.index(track.pk))
        return sorted_tracks

    context['hot_tracks'] += get_sorted_tracks_from_actions(like_friends_qs)
    if len(context['hot_tracks']) < 8:
        context['hot_tracks'] += get_sorted_tracks_from_actions(like_friends_qs)

    if 'page' not in request.GET: 
        template_name = 'me.html'

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

@decorators.login_required
def user_settings(request, username, form_class=UserSettingsForm,
    template_name='user_settings.html', extra_context=None):

    context = {}
    instance = shortcuts.get_object_or_404(User, username=username)
    if instance != request.user and not request.user.is_staff:
        return http.HttpResponseForbidden()
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.INFO, 
                u'Thanks for updating your settings')
    else:
        form = form_class(instance=instance)
    context['form'] = form
    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

@decorators.login_required
def user_delete(request, username,
    template_name='user_delete.html', extra_context=None):

    context = {}
    instance = shortcuts.get_object_or_404(User, username=username)
    if instance != request.user and not request.user.is_staff:
        return http.HttpResponseForbidden()

    root = User.objects.get(pk=settings.ROOT_USERID)
   
    context['status'] = 'toconfirm'
    if request.method == 'POST':
        if request.POST.get('confirm', False):
            instance.playlist_set.all().update(creation_user=root)
            instance.delete()
            messages.add_message(request, messages.INFO, 
                u'Your account was deleted. There is no going back.')
            context['status'] = 'deleted'
    
    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

