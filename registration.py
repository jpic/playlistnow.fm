import httplib2
import logging
import gfc
import opensocial
import urllib
import simplejson
import operator

from django import http
from django import shortcuts
from django import template
from django import forms
from django.contrib import auth
from django.conf import settings
from django.core import urlresolvers
from django.template import defaultfilters
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf.urls.defaults import patterns, url

from actstream.models import follow
from socialregistration.utils import OAuthTwitter

logger = logging.getLogger(__name__)

def get_next_step(request):
    if not 'socialregistration_profile' in request.session:
        return 'acct_signup'
    elif not 'socialregistration_userdata' in request.session:
        return 'socialregistration_userdata'
    elif not 'socialregistration_friends' in request.session:
        return 'socialregistration_friends'
    else:
        return 'socialregistration_complete'

class UserDataForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    location = forms.CharField()
    email = forms.EmailField()
    avatar_url = forms.CharField(widget=forms.HiddenInput)
    url = forms.CharField(widget=forms.HiddenInput)
    nick = forms.CharField(widget=forms.HiddenInput)

class RegistrationMiddleware(object):
    def process_request(self, request):
        # if the user is in registration process
        if 'socialregistration_user' in request.session:
            # if he's not submitting a form
            if request.method != 'POST':
                # then we should redirect him to the appropriate form
                if 'socialregistration_userdata' not in request.session:
                    return http.HttpResponseRedirect(urlresolvers.reverse(
                        'socialregistration_userdata'))
                elif 'socialregistration_friends' not in request.session:
                    return http.HttpResponseRedirect(urlresolvers.reverse(
                        'socialregistration_friends'))
                else: # we want to log him in
                    return http.HttpResponseRedirect(urlresolvers.reverse(
                        'socialregistration_complete'))

def socialregistration_userdata(request, form_class=UserDataForm,
    template_name='socialregistration/userdata.html', extra_context=None):
    context = {}

    if 'socialregistration_profile' in request.session:
        profile = request.session['socialregistration_profile']
        user = request.session['socialregistration_user']
    elif request.user.is_authenticated():
        if request.user.facebookprofile_set.count():
            profile = request.user.facebookprofile_set.all()[0]
        elif request.user.twitterprofile_set.count():
            profile = request.user.twitterprofile_set.all()[0]
        if request.user.la_facebookprofile_set.count():
            profile = request.user.la_facebookprofile_set.all()[0]
        user = request.user
    else:
        return http.HttpResponseRedirect(urlresolvers.reverse(
            'acct_signup'))

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            request.session['socialregistration_userdata'] = form.cleaned_data
            
            user = request.session['socialregistration_user']
            profile = request.session['socialregistration_profile']
            userdata = request.session['socialregistration_userdata']

            user.first_name = userdata.get('first_name', '')
            user.last_name = userdata.get('last_name', '')
            user.email = userdata.get('email', '')
            user_slug = defaultfilters.slugify('%s %s' % (
                user.first_name,
                user.last_name
            ))
            if User.objects.filter(username=user_slug).count() > 0:
                i = 1
                user_slug_test = user_slug + unicode(i)
                while User.objects.filter(username=user_slug_test).count() >0:
                    i += 1
                    user_slug_test = user_slug + str(i)
                user.username = user_slug_test
            else:
                user.username = user_slug
            user.save()

            user.playlistprofile.user_location = userdata.get('location', '')
            user.playlistprofile.avatar_url = userdata.get('avatar_url', '')
            user.playlistprofile.user = user
            user.playlistprofile.save()

            profile.user = user
            profile.avatar_url = userdata.get('avatar_url', '')
            profile.url = userdata.get('url', '')
            profile.nick = userdata.get('nick', '')
            profile.save()

            if 'socialregistration_user' in request.session: 
                del request.session['socialregistration_user']
            if 'socialregistration_profile' in request.session: 
                del request.session['socialregistration_profile']
            if 'socialregistration_userdata' in request.session: 
                del request.session['socialregistration_userdata']

            user = profile.authenticate()
            auth.login(request, user)
            request.user = user

            if not user:
                logger.info('NOT USER IN REGISTRATION!')
                return shortcuts.render_to_response('socialregistration/fail.html', context,
                    context_instance=template.RequestContext(request))

            friends = []
            conditions = []
             
            for facebookprofile in user.userassociation_set.all():
                h = httplib2.Http()
                resp, ct = h.request('https://graph.facebook.com/me/friends?' 
                    + urllib.urlencode({'access_token': facebookprofile.token,}))
                facebook_ids = [x['id'] for x in simplejson.loads(ct)['data']]
                conditions.append(Q(facebookprofile__uid__in=facebook_ids))

            try:
                if user.twitterprofile_set.count():
                    client = OAuthTwitter(
                        request, settings.TWITTER_CONSUMER_KEY,
                        settings.TWITTER_CONSUMER_SECRET_KEY,
                        settings.TWITTER_REQUEST_TOKEN_URL,
                    )
                for twitterprofile in user.twitterprofile_set.all():
                    res = simplejson.loads(client.query('http://api.twitter.com/1/statuses/friends.json'))
                    twitter_ids = [x['id'] for x in res]
                    conditions.append(Q(twitterprofile__twitter_id__in=twitter_ids))
            
                for gfcprofile in user.gfcprofile_set.all():
                    container = gfc.my_opensocial_container(request)
                    res = container.fetch_friends()
                    gfc_ids = [x['id'] for x in res]
                    conditions.append(Q(gfcprofile__uid__in=gfc_ids))
            except:
                pass

            
            for u in User.objects.filter(reduce(operator.or_,conditions)):
                follow(user, u)

            return http.HttpResponseRedirect(urlresolvers.reverse('socialregistration_friends'))
    else:
        if profile.__class__.__name__ == 'FacebookProfile':
            upstream = request.facebook.graph.request(request.facebook.user['uid'])
            initial = {
                'first_name': upstream.get('first_name', ''),
                'last_name': upstream.get('last_name', ''),
                'email': upstream.get('email', ''),
                'avatar_url': 'http://graph.facebook.com/%s/picture' % request.facebook.user['uid'],
                'nick': '%s %s' % (upstream.get('first_name', ''), upstream.get('last_name', '')),
                'url': upstream.get('link', ''),
            }
            if 'location' in upstream:
                initial['location'] = upstream['location']['name']
            else:   
                initial['location'] = ''

        elif profile.__class__.__name__ == 'TwitterProfile':
            client = OAuthTwitter(
                request, settings.TWITTER_CONSUMER_KEY,
                settings.TWITTER_CONSUMER_SECRET_KEY,
                settings.TWITTER_REQUEST_TOKEN_URL,
            )
            upstream = client.get_user_info()
            initial = {
                'first_name': '',
                'last_name': upstream.get('name', ''),
                'location': upstream.get('location', ''),
                'email': '',
                'avatar_url': upstream['profile_image_url'],
                'url': 'http://twitter.com/%s' % upstream['screen_name'],
                'nick': upstream['screen_name'],
            }

        elif profile.__class__.__name__ == 'GfcProfile':
            container = la_facebook.my_opensocial_container(request)
            req = opensocial.FetchPersonRequest(profile.uid, ['@all'])
            upstream = container.send_request(req)
            initial = {
                'first_name': upstream.get('displayName', ''),
                'last_name': '',
                'location': '',
                'email': '',
                'avatar_url': upstream['thumbnailUrl'],
                'url': upstream['urls'][0]['value'],
                'nick': upstream['displayName'],
            }
        form = form_class(initial=initial)

    context['form'] = form
    context['step'] = 'userdata'

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def socialregistration_friends(request,
    template_name='socialregistration/friends.html', extra_context=None):
    context = {}

    friends = []
    conditions = []
    user = request.user
    
    for facebookprofile in user.userassociation_set.all():
        h = httplib2.Http()
        resp, ct = h.request('https://graph.facebook.com/me/friends?' 
            + urllib.urlencode({'access_token': facebookprofile.token,}))
        facebook_ids = [x['id'] for x in simplejson.loads(ct)['data']]
        conditions.append(Q(facebookprofile__uid__in=facebook_ids))

    try:
        if user.twitterprofile_set.count():
            client = OAuthTwitter(
                request, settings.TWITTER_CONSUMER_KEY,
                settings.TWITTER_CONSUMER_SECRET_KEY,
                settings.TWITTER_REQUEST_TOKEN_URL,
            )
        for twitterprofile in user.twitterprofile_set.all():
            res = simplejson.loads(client.query('http://api.twitter.com/1/statuses/friends.json'))
            twitter_ids = [x['id'] for x in res]
            conditions.append(Q(twitterprofile__twitter_id__in=twitter_ids))

        for gfcprofile in user.gfcprofile_set.all():
            container = gfc.my_opensocial_container(request)
            res = container.fetch_friends()
            gfc_ids = [x['id'] for x in res]
            conditions.append(Q(gfcprofile__uid__in=gfc_ids))
    except: 
        pass

    context['friends'] = User.objects.filter(reduce(operator.or_,conditions))
    context['follows'] = [f.actor for f in user.follow_set.all()]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def socialregistration_complete(request,
    template_name='socialregistration/complete.html', extra_context=None):
    context = {}

    # handle friends here

    context['force_reload'] = True

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def socialregistration_cancel(request,
    template_name='socialregistration/cancel.html', extra_context=None):
    context = {}

    # don't cancel if the registration is complete
    if 'socialregistration_user' in request.session and \
       'socialregistration_profile' in request.session and \
       'socialregistration_userdata' in request.session:
        request.session['socialregistration_cancelattempt'] = True
        return http.HttpResponseRedirect(urlresolvers.reverse(
            'socialregistration_complete'))

    if request.method == 'POST' and request.POST.get('confirm', False):
        if 'socialregistration_user' in request.session: 
            del request.session['socialregistration_user']
        if 'socialregistration_profile' in request.session: 
            del request.session['socialregistration_profile']
        if 'socialregistration_userdata' in request.session: 
            del request.session['socialregistration_userdata']
        # socialregistration_friends intentionally omited because it would
        # mean that registration is complete

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))


urls = patterns('',
    url( # overload original socialregistration_setup url
        'setup/$', 
        socialregistration_userdata,
        name='socialregistration_setup'
    ),
    url(
        'userdata/$', 
        socialregistration_userdata,
        name='socialregistration_userdata'
    ),
    url(
        'friends/$', 
        socialregistration_friends,
        name='socialregistration_friends'
    ),
    url(
        'cancel/$', 
        socialregistration_cancel,
        name='socialregistration_cancel'
    ),
    url(
        'complete/$', 
        socialregistration_complete,
        name='socialregistration_complete'
    ),
)
