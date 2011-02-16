import simplejson
from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.core import urlresolvers
from django.template import defaultfilters
from django.conf import settings
from django.contrib.comments.managers import CommentManager
from django.core.cache import cache

from music.models import Track, Artist
from tagging.fields import TagField
from notification import models as notification

from actstream.models import Follow
from socialregistration.models import TwitterProfile, FacebookProfile

TwitterProfile.add_to_class('avatar_url', models.TextField(null=True, blank=True))
FacebookProfile.add_to_class('avatar_url', models.TextField(null=True, blank=True))
TwitterProfile.add_to_class('nick', models.TextField(null=True, blank=True))
FacebookProfile.add_to_class('nick', models.TextField(null=True, blank=True))
TwitterProfile.add_to_class('url', models.TextField(null=True, blank=True))
FacebookProfile.add_to_class('url', models.TextField(null=True, blank=True))

def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type("new_comment", "Comment posted", "Another member comments one of your actions")
    notification.create_notice_type("new_follower", "New follower", "Another member follows you")
    notification.create_notice_type("yourplaylist_bookmarked", "Bookmarked your playlist", "Another member bookmarks your playlist")
    notification.create_notice_type("new_message", "New message", "Another member posted on your wall")
    notification.create_notice_type("new_recomandation", "New recomandation", "A friend recomands you a particular song")
    notification.create_notice_type("new_thanks", "You were thanked", "Another member thanked you for your contribution")
signals.post_syncdb.connect(create_notice_types, sender=notification)

def new_comment(sender, instance, created, **kwargs):
    context = {}
    recipients = []

    # notify all users who commented the same object
    for comment in instance._default_manager.for_model(instance.content_object):
        if comment.user not in recipients and comment.user != instance.user:
            recipients.append(comment.user)

    # if the object is a user action then also notify the actor
    if instance.content_object.__class__.__name__ == 'Action':
        instance.content_object.timestamp = datetime.now()
        instance.content_object.save()

        if instance.content_object.actor.__class__.__name__ == 'User' and \
            instance.content_object.actor not in recipients and \
            instance.content_object.actor != instance.user:
            recipients.append(instance.content_object.actor)
        if instance.content_object.action_object.__class__.__name__ == 'User' and \
            instance.content_object.action_object not in recipients and \
            instance.content_object.action_object != instance.user:
            recipients.append(instance.content_object.action_object)
            context['url'] = urlresolvers.reverse(
                'user_details', args=(instance.content_object.action_object.username,))
        if instance.content_object.target.__class__.__name__ == 'User' and \
            instance.content_object.target not in recipients and \
            instance.content_object.target != instance.user:
            recipients.append(instance.content_object.target)
            context['url'] = urlresolvers.reverse(
                'user_details', args=(instance.content_object.target.username,))

    context['comment'] = instance

    notification.send(recipients, 'new_comment', context)
signals.post_save.connect(new_comment, sender=models.get_model('comments', 'Comment'))

def affinities_betwen(profile1, profile2):
    key1 = '%s and %s affinities' % (profile1.pk, profile2.pk)
    key2 = '%s and %s affinities' % (profile2.pk, profile1.pk)

    result1 = cache.get(key1)
    if result1:
        return result1
    result2 = cache.get(key2)
    if result2:
        return result2

    factors = []

    profile1_tracks_count = profile1.tiny_playlist.tracks.count()
    profile2_tracks_count = profile2.tiny_playlist.tracks.count()
    if profile1_tracks_count and profile2_tracks_count:
        comon_tracks_count = float(Track.objects.filter(playlist=profile1.tiny_playlist).filter(playlist=profile2.tiny_playlist).count())
        comon_tracks_factor = comon_tracks_count / profile1_tracks_count + comon_tracks_count / profile2_tracks_count
        factors.append(comon_tracks_factor)
        #print profile1_tracks_count, comon_tracks_count, profile2_tracks_count, comon_tracks_factor

    profile1_artists_count = profile1.fanof_artists.count()
    profile2_artists_count = profile2.fanof_artists.count()
    if profile1_artists_count and profile2_artists_count:
        comon_artists_count = float(Artist.objects.filter(fans=profile1).filter(fans=profile2).count())
        comon_artists_factor = comon_artists_count / profile1_artists_count + comon_artists_count / profile2_artists_count
        factors.append(comon_artists_factor)
        #print profile1_artists_count, comon_artists_count, profile2_artists_count, comon_artists_factor

    profile1_playlists_count = profile1.fanof_playlists.count()
    profile2_playlists_count = profile2.fanof_playlists.count()
    if profile1_playlists_count and profile2_playlists_count:
        comon_playlists_count = float(Playlist.objects.filter(fans=profile1).filter(fans=profile2).count())
        comon_playlists_factor = comon_playlists_count / profile1_playlists_count + comon_playlists_count / profile2_playlists_count
        factors.append(comon_playlists_factor)
        #print profile1_playlists_count, comon_playlists_count, profile2_playlists_count, comon_playlists_factor

    # actually that would be len(factors) * 2 if we did not want to intentionnaly increase the affinities :D
    if len(factors):
        percent = int((sum(factors) / len(factors)) * 100)
    else:
        percent = 0
    #print percent

    if percent > 100:
        percent = 100

    #cache.set(key1, percent, 7200)

    return percent

class PlaylistProfile(models.Model):
    user = models.OneToOneField('auth.User', verbose_name=_(u'user'))
    user_location = models.CharField(max_length=100, verbose_name=_(u'location'), null=True, blank=True)
    tiny_playlist = models.ForeignKey('Playlist', related_name='favorite_of')
    fanof_playlists = models.ManyToManyField('playlist.Playlist', verbose_name=_(u'fav playlists'), null=True, blank=True, related_name='fans')
    fanof_artists = models.ManyToManyField('music.Artist', verbose_name=_(u'fav artists'), null=True, blank=True, related_name='fans')
    fanof_actions = models.ManyToManyField('actstream.Action', null=True, blank=True, related_name='fans')

    last_playlist = models.ForeignKey('playlist.Playlist', verbose_name=_(u'last playlist'), null=True, blank=True)
    avatar_url = models.TextField(null=True, blank=True, default='/site_media/static/images/avatar-logged.jpg')

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def get_absolute_url(self):
        return urlresolvers.reverse('user_details', args=(self.user.username,))

    def friends(self):
        follows_users_ids = Follow.objects.filter(user=self.user,
                                                  content_type__app_label='auth',
                                                  content_type__model='user') \
                                          .exclude(object_id=self.user.pk) \
                                          .values_list('object_id', flat=True)
        c = ContentType.objects.get_for_model(User)
        target_choices_qs = User.objects.filter(
            Q(follow__object_id=self.user.pk, follow__content_type=c) | 
            Q(id__in=follows_users_ids)
        ).select_related('playlistprofile')
        return target_choices_qs

def autoprofile(sender, instance, **kwargs):
    try:
        instance.playlistprofile
    except PlaylistProfile.DoesNotExist:
        tiny_playlist = Playlist(
            name='hidden:tiny',
            creation_user=instance,
            slug='tiny'
        )
        tiny_playlist.save()

        instance.playlistprofile = PlaylistProfile(
            user=instance,
            tiny_playlist=tiny_playlist
        )
        instance.playlistprofile.save()
signals.post_save.connect(autoprofile, sender=models.get_model('auth','user'))

class PlaylistCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=_(u'name'))
    parent = models.ForeignKey('PlaylistCategory', verbose_name=_(u'parent'), null=True, blank=True, related_name='children')
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'), null=True, blank=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        try:
            return urlresolvers.reverse('playlist_category_details_with_parent', 
                args=(self.parent.slug, self.slug,))
        except PlaylistCategory.DoesNotExist:
            return urlresolvers.reverse('playlist_category_details', 
                args=(self.slug,))

class PlaylistModification(models.Model):
    ACTIONS = (
        ('add', _('add')),
        ('rm', _('remove')),
    )

    playlist = models.ForeignKey('Playlist')
    track = models.ForeignKey('music.Track')
    creation_user = models.ForeignKey('auth.User', verbose_name=_(u'creator'))
    creation_datetime = models.DateTimeField(verbose_name=_(u'published'), auto_now_add=True)
    action = models.CharField(max_length=3, choices=ACTIONS)

    class Meta:
        ordering = ('creation_datetime',)

    def __unicode__(self):
        return u'proposal: %s track %s to %s, by %s' % (
            self.get_action_display(),
            self.track,
            self.playlist,
            self.creation_user
        )

class PlaylistManager(models.Manager):
    def get_query_set(self):
        return super(PlaylistManager, self).get_query_set().exclude(name__istartswith='hidden:')

    def all_with_hidden(self):
        return super(PlaylistManager, self).get_query_set()

class Playlist(models.Model):
    tracks = models.ManyToManyField('music.Track', verbose_name=_(u'tracks'), null=True, blank=True)
    category = models.ForeignKey(PlaylistCategory, verbose_name=_(u'category'), null=True, blank=True)
    play_counter = models.IntegerField(verbose_name=_(u'played'), default=0)
    
    creation_user = models.ForeignKey('auth.User', verbose_name=_(u'creator'))
    creation_datetime = models.DateTimeField(verbose_name=_(u'published'), auto_now_add=True)
    modification_datetime = models.DateField(verbose_name=_(u'modified'), auto_now=True)

    name = models.CharField(max_length=100, verbose_name=_(u'name'))
    slug = models.CharField(max_length=100, verbose_name=_(u'slug'))
    image = models.ImageField(verbose_name=_(u'icon'), null=True, blank=True, upload_to='playlist_images')

    unique_autoslug = False

    tags = TagField()

    objects = PlaylistManager()

    def __unicode__(self):
        if self.name == 'hidden:tiny':
            return "Tiny playlist: I am %s %s" % (self.creation_user.first_name, self.creation_user.last_name)
        return u'I am %s' % self.name

    class Meta:
        ordering = ('name',)

    def get_absolute_url(self):
        return urlresolvers.reverse('playlist_details', args=(
            self.creation_user.username, self.slug,))

    def to_json_dict(self, **kwargs):
        return simplejson.dumps(self.to_dict(**kwargs))

    def to_dict(self, with_tracks=True, with_tracks_artist=True,
        with_tracks_youtube_best_id=True, for_user=None):
        data = {}
        data['object'] = {
            'name': unicode(self),
            'url': self.get_absolute_url(),
            'pk': self.pk,
        }
        data['tracks'] = []

        if with_tracks:
            if for_user:
                tracks = self.all_user_tracks(for_user)
            else:
                tracks = self.tracks.model.objects.filter(playlist=self).select_related()

            for track in tracks:
                data['tracks'].append(track.to_dict(
                    with_artist=with_tracks_artist,
                    with_youtube_best_id=with_tracks_youtube_best_id
                ))

        return data

    def added_user_tracks(self, user):
        return self.__class__.tracks.field.rel.to.objects.filter(self.added_user_tracks_condition(user))

    def added_user_tracks_condition(self, user):
        return Q(playlistmodification__playlist=self) & Q(playlistmodification__creation_user=user) & Q(playlistmodification__action='add')

    def removed_user_tracks(self, user):
        return self.__class__.tracks.field.rel.to.objects.filter(self.removed_user_tracks_condition(user))

    def removed_user_tracks_condition(self, user):
        return Q(playlistmodification__playlist=self) & Q(playlistmodification__creation_user=user) & Q(playlistmodification__action='rm')

    def all_user_tracks(self, user):
        return self.__class__.tracks.field.rel.to.objects.filter(
            (
                Q(playlist=self) | 
                self.added_user_tracks_condition(user)
            ) & ~self.removed_user_tracks_condition(user)
        ).select_related().distinct()

def autoslug(sender, instance, **kwargs):
    if not hasattr(instance, 'slug'):
        return True
    
    if not getattr(instance.__class__, 'autoslug', True):
        return True

    if getattr(instance, 'name') == 'hidden:tiny' and instance.creation_user.username:
        instance.slug = instance.creation_user.username
    elif hasattr(instance, 'name'):
        instance.slug = defaultfilters.slugify(instance.name)
    
    if not instance.slug:
        instance.slug = instance.pk

    if not getattr(instance.__class__, 'unique_autoslug', False):
        return True

    while instance.__class__.objects.filter(slug=instance.slug).count():
        instance.slug += '-'

signals.pre_save.connect(autoslug)


from actstream import action

def playlist_create_activity(sender, instance, created, **kwargs):
    if created and not 'hidden:' in instance.name:
        action.send(instance.creation_user, verb=u'created playlist', target=instance)
signals.post_save.connect(playlist_create_activity, sender=Playlist)

def last_playlist(sender, instance, action, **kwargs):
    if action == 'post_add':
        for pk in kwargs.pop('pk_set'):
            a = Playlist.tracks.field.rel.to.objects.get(pk=pk).artist
            a.last_playlist = instance
            a.save()
signals.m2m_changed.connect(last_playlist, sender=Playlist.tracks.through)
