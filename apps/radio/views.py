from django import http
from django import shortcuts
from django import template
from django.db.models import get_model
from django.db.models import Q
from django.template import defaultfilters
from django.contrib.auth import decorators
from django.conf import settings
from django.utils import simplejson
from django.contrib import messages

from music.models import *
from playlist.models import *

def radio_artist(request, name, tab='overview', paginate_by=10,
    template_name='music/artist_details.html', extra_context=None):

    name = name.strip()

    if 'format' not in request.GET.keys():
        return http.HttpResponse(u'We need to upgrade your javascript. <a class="ui_ignore" href="http://playlistnow.fm/music/artist/%s/">click here to continue</a>' % name)

    # magic user holds all radios
    radio, created = User.objects.get_or_create(username='radio')

    # try to get cachable playlist
    try:
        playlist = radio.playlist_set.get(name=name, creation_user=radio)
    except Playlist.DoesNotExist:
        playlist = Playlist(name=name, creation_user=radio)
        playlist.save()

    # just need artist tracks
    lastfm_error = False
    try:
        artist = Artist.objects.get(name__iexact=name)
    except Artist.DoesNotExist:
        artist = Artist(name=name)
        artist.save()

    try:
        artist.lastfm_get_tracks()
    except:
        lastfm_error = True

    saved_tracks = artist.track_set.all()
    if len(saved_tracks) < 7:
        youtube_calls = 7
    else:
        youtube_calls = 3
    for track in artist.tracks:
        for saved_track in saved_tracks:
            if saved_track.name.lower() == track.name.lower():
                continue

        try:
            track = Track.objects.get(artist=artist, name__iexact=track.name.strip())
        except Track.DoesNotExist:
            track = Track(artist=artist, name=track.name)
        
        if not track.youtube_id:
            track.youtube_id = track.youtube_get_best()
            youtube_calls -= 1
            try:
                track.save()
            except:
                continue

        playlist.tracks.add(track)

        if youtube_calls == 0:
            break

    if request.user.is_authenticated():
        serialized = playlist.to_dict(for_user=request.user)
    else:
        serialized = playlist.to_dict()

    serialized['radio_artist'] = name
    serialized['object']['radioUrl'] = urlresolvers.reverse('radio_artist', args=(name,))

    return http.HttpResponse(simplejson.dumps(serialized), status=200)
