import logging
import gfc
import opensocial

from django import http
from django import shortcuts
from django import template
from django import forms
from django.contrib import auth
from django.conf import settings
from django.core import urlresolvers
from django.template import defaultfilters
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf.urls.defaults import patterns, url

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
        profile = request.session['socialregistration_profile']
        user = request.session['socialregistration_user']
    else:
        return http.HttpResponseRedirect(urlresolvers.reverse(
            'acct_signup'))

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            logging.debug('valid form')
            request.session['socialregistration_userdata'] = form.cleaned_data
            logging.debug('set socialregistration_userdata session')

            user = request.session['socialregistration_user']
            profile = request.session['socialregistration_profile']
            userdata = request.session['socialregistration_userdata']

            logger.debug('user', request.session['socialregistration_user'])
            logger.debug('profile', request.session['socialregistration_profile'])
            logger.debug('userdata', request.session['socialregistration_userdata'])

            user.first_name = userdata['first_name']
            user.last_name = userdata['last_name']
            user.email = userdata['email']
            user_slug = defaultfilters.slugify('%s %s' % (
                user.first_name,
                user.last_name
            ))
            if User.objects.filter(username=user_slug).count() > 0:
                i = 1
                user_slug_test = user_slug + unicode(i)
                while User.objects.filter(username=user_slug_test).count() >0:
                    i += 1
                    user_slug_test = user_slug + i
                user.username = user_slug_test
            else:
                user.username = user_slug
            user.save()
            logger.info('saved user', user)

            user.playlistprofile.user_location = userdata['location']
            user.playlistprofile.avatar_url = userdata['avatar_url']
            user.playlistprofile.user = user
            user.playlistprofile.save()
            logger.info('saved playlistprofile', user.playlistprofile)

            profile.user = user
            profile.save()
            logger.info('saved profile', profile)


            if 'socialregistration_user' in request.session: 
                del request.session['socialregistration_user']
            if 'socialregistration_profile' in request.session: 
                del request.session['socialregistration_profile']
            if 'socialregistration_userdata' in request.session: 
                del request.session['socialregistration_userdata']

            user = profile.authenticate()
            logger.info('authenticated %s' % user)
            auth.login(request, user)
            request.user = user
            logger.info('logged in %s' % user)

            return http.HttpResponseRedirect(urlresolvers.reverse('socialregistration_friends'))
        else:
            logging.debug('invalid form')
    else:
        if profile.__class__.__name__ == 'FacebookProfile':
            upstream = request.facebook.graph.request(request.facebook.user['uid'])
            initial = {
                'first_name': upstream['first_name'],
                'last_name': upstream['last_name'],
                'location': upstream['location']['name'],
                'email': upstream['email'],
                'avatar_url': '/site_media/static/images/avatar-logged.jpg',
            }

        elif profile.__class__.__name__ == 'TwitterProfile':
            client = OAuthTwitter(
                request, settings.TWITTER_CONSUMER_KEY,
                settings.TWITTER_CONSUMER_SECRET_KEY,
                settings.TWITTER_REQUEST_TOKEN_URL,
            )
            upstream = client.get_user_info()
            initial = {
                'first_name': upstream['name'],
                'last_name': upstream['name'],
                'location': upstream['location'],
                'email': '',
                'avatar_url': upstream['profile_image_url'],
            }

        elif profile.__class__.__name__ == 'GfcProfile':
            container = gfc.my_opensocial_container(request)
            req = opensocial.FetchPersonRequest(profile.uid, ['@all'])
            upstream = container.send_request(req)
            initial = {
                'first_name': upstream['displayName'],
                'last_name': upstream['displayName'],
                'location': '',
                'email': '',
                'avatar_url': upstream['thumbnailUrl'],
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
    user = request.user
    
    for facebookprofile in user.facebookprofile_set.all():
        friendlist = request.facebook.graph.request(request.facebook.user['uid'] + '/friends')
        facebook_ids = [x['id'] for x in friendlist['data']]
        logging.info("Facebook ids %s" % facebook_ids)
        #(facebookprofile__in=facebook_ids)


    if user.twitterprofile_set.count():
        client = OAuthTwitter(
            request, settings.TWITTER_CONSUMER_KEY,
            settings.TWITTER_CONSUMER_SECRET_KEY,
            settings.TWITTER_REQUEST_TOKEN_URL,
        )
    for twitterprofile in user.twitterprofile_set.all():
        res = client.query('http://api.twitter.com/1/statuses/friends.json')
        logger.info('twitter res %s' % res)

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

    logger.info('user attempts to cancel registration')
    # don't cancel if the registration is complete
    if 'socialregistration_user' in request.session and \
       'socialregistration_profile' in request.session and \
       'socialregistration_userdata' in request.session:
        logger.info('a user wanted to cancel registration, but it is complete')
        request.session['socialregistration_cancelattempt'] = True
        return http.HttpResponseRedirect(urlresolvers.reverse(
            'socialregistration_complete'))

    if request.user.is_authenticated():
        logger.info('an authenticated user tried to cancel registration')

    if request.method == 'POST' and request.POST.get('confirm', False):
        if 'socialregistration_user' in request.session: 
            del request.session['socialregistration_user']
        if 'socialregistration_profile' in request.session: 
            del request.session['socialregistration_profile']
        if 'socialregistration_userdata' in request.session: 
            del request.session['socialregistration_userdata']
        # socialregistration_friends intentionally omited because it would
        # mean that registration is complete
        logger.info('user canceled registration')
    else:
        logger.info('asking for confirmation')

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