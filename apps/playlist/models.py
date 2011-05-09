import simplejson
import operator
import urllib
from datetime import datetime

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import signals, Q, Count
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
from actstream import action
from socialregistration.models import TwitterProfile, FacebookProfile

TwitterProfile.add_to_class('access_token', models.TextField(help_text='only useful if your app wants to tweet while the browser is not authenticated via twitter', null=True, blank=True))
TwitterProfile.add_to_class('token_secret', models.TextField(help_text='only useful if your app wants to tweet while the browser is not authenticated via twitter', null=True, blank=True))
TwitterProfile.add_to_class('avatar_url', models.TextField(null=True, blank=True))
FacebookProfile.add_to_class('avatar_url', models.TextField(null=True, blank=True))
TwitterProfile.add_to_class('nick', models.TextField(null=True, blank=True))
FacebookProfile.add_to_class('nick', models.TextField(null=True, blank=True))
TwitterProfile.add_to_class('url', models.TextField(null=True, blank=True))
FacebookProfile.add_to_class('url', models.TextField(null=True, blank=True))

def new_user_unicode(self):
    return '%s %s' % (self.first_name, self.last_name)
User.__unicode__ = new_user_unicode

def new_user_get_absolute_url(self):
    return urlresolvers.reverse('user_details', args=(self.username,))
User.get_absolute_url = new_user_get_absolute_url

def twitter_url(sender, instance, **kwargs):
    if instance.nick:
        instance.url = 'http://twitter.com/%s' % instance.nick
signals.pre_save.connect(twitter_url, sender=TwitterProfile)

def create_notice_types(app, created_models, verbosity, **kwargs):
    notification.create_notice_type("new_comment", "Comment posted", "Another member comments one of your actions")
    notification.create_notice_type("new_follower", "New follower", "Another member follows you")
    notification.create_notice_type("yourplaylist_bookmarked", "Bookmarked your playlist", "Another member bookmarks your playlist")
    notification.create_notice_type("new_message", "New message", "Another member posted on your wall")
    notification.create_notice_type("new_recommendation", "New recommendation", "A friend recommends you a particular song")
    notification.create_notice_type("new_thanks", "You were thanked", "Another member thanked you for your contribution")
signals.post_syncdb.connect(create_notice_types, sender=notification)

def new_thanks(sender, instance, created, **kwargs):
    if created:
        return None
    if not instance.thanks:
        return None

    recipients = [instance.source]
    context = {
        'recommendation': instance,
        'site': Site.objects.get_current(),
    }

    notification.send(recipients, 'new_thanks', context)
signals.post_save.connect(new_thanks, sender=models.get_model('music', 'Recommendation'))

def user_delete(sender, instance, **kwargs):
    Action = models.get_model('actstream', 'Action')
    Follow = models.get_model('actstream', 'Follow')
    Comment = models.get_model('comments', 'Comment')
    c = ContentType.objects.get_for_model(User)

    Follow.objects.filter(user=instance).delete()
    Follow.objects.filter(content_type=c, object_id=instance.pk).delete()
    Comment.objects.filter(content_type=c, object_pk=instance.pk).delete()
    Action.objects.filter(actor_content_type=c, actor_object_id=instance.pk).delete()
    Action.objects.filter(target_content_type=c, target_object_id=instance.pk).delete()
    Action.objects.filter(action_object_content_type=c, action_object_object_id=instance.pk).delete()

signals.pre_delete.connect(user_delete, sender=models.get_model('auth', 'User'))

def new_recommendation(sender, instance, created, **kwargs):
    if not created:
        return None

    recipients = [instance.target]
    context = {
        'recommendation': instance,
        'site': Site.objects.get_current(),
    }

    notification.send(recipients, 'new_recommendation', context)
signals.post_save.connect(new_recommendation, sender=models.get_model('music', 'Recommendation'))

def yourplaylist_bookmarked(sender, instance, **kwargs):
    if sender.__name__ != 'PlaylistProfile_fanof_playlists':
        return None
    if kwargs['action'] != 'post_add':
        return None

    recipients = [instance.creation_user]

    for pk in kwargs['pk_set']:
        context = {
            'playlist': instance,
            'user': User.objects.get(playlistprofile__pk=pk),
            'site': Site.objects.get_current(),
        }
        instance.creation_user.playlistprofile.points += 3
        instance.creation_user.playlistprofile.save()

        notification.send(recipients, 'yourplaylist_bookmarked', context)
signals.m2m_changed.connect(yourplaylist_bookmarked)

def update_counts(sender, instance, **kwargs):
    if kwargs['action'] != 'post_add' and kwargs['action'] != 'post_remove':
        return None

    if sender.__name__ == 'Playlist_tracks':
        instance.tracks_count = instance.tracks.count()
    elif sender.__name__ == 'Playlist_fans':
        instance.fans_count = instance.fans.count()
    else:
        return None
    
    instance.save()
signals.m2m_changed.connect(update_counts)

def new_follower(sender, instance, created, **kwargs):
    if not created:
        return None
    if not instance.__class__.__name__ == 'Follow':
        return None
    if not instance.actor.__class__.__name__ == 'User':
        return None

    recipients = [instance.actor]
    context = {
        'follow': instance,
        'site': Site.objects.get_current(),
    }

    notification.send(recipients, 'new_follower', context)
signals.post_save.connect(new_follower, sender=models.get_model('activity', 'Follow'))

def new_comment(sender, instance, created, **kwargs):
    if not created:
        return None
    if not instance.__class__.__name__ == 'Comment':
        return None

    context = {
        'comment': instance,
        'site': Site.objects.get_current(),
    }
    recipients = []

    # notify all users who commented the same object
    for comment in instance._default_manager.for_model(instance.content_object):
        if comment.user not in recipients and comment.user != instance.user:
            recipients.append(comment.user)

    # if the object is a user action then also notify the actor
    if instance.content_object.__class__.__name__ == 'Action':
        activity = instance.content_object
        context['url'] = activity.actor.get_absolute_url()
        update_timestamp_pks = [activity.pk]
        
        group_verbs = ('liked track', 'added track to playlist', 'becomes fan of artist')
        if activity.verb in group_verbs:
            next_instances = activity.__class__.objects.filter(
                actor_content_type = activity.actor_content_type,
                actor_object_id = activity.actor_object_id,
                pk__gt = activity.pk
            )[:15]
            for next_instance in next_instances:
                if next_instance.verb != activity.verb:
                    break
                update_timestamp_pks.append(next_instance.pk)
        update_timestamp_qs = activity.__class__.objects.filter(pk__in=update_timestamp_pks)
        update_timestamp_qs.update(timestamp=datetime.now())

        if instance.content_object.actor.__class__.__name__ == 'User' and \
            instance.content_object.actor not in recipients and \
            instance.content_object.actor != instance.user:
            recipients.append(instance.content_object.actor)

        if instance.content_object.action_object.__class__.__name__ == 'User' and \
            instance.content_object.action_object not in recipients and \
            instance.content_object.action_object != instance.user:
            recipients.append(instance.content_object.action_object)
        if instance.content_object.target.__class__.__name__ == 'User' and \
            instance.content_object.target not in recipients and \
            instance.content_object.target != instance.user:
            recipients.append(instance.content_object.target)
        context['activity'] = instance.content_object
        notification.send(recipients, 'new_comment', context)

    # if the object is a user then create a wall post activity and notify him
    elif instance.content_object.__class__.__name__ == 'User':
        if instance.content_object != instance.user:
            context['comment'] = instance
            recipients = [instance.content_object]
            action.send(instance.user, verb='wall posted', target=instance.content_object, action_object=instance)
            notification.send(recipients, 'new_message', context)

signals.post_save.connect(new_comment, sender=models.get_model('comments', 'Comment'))

def new_follow(sender, instance, created, **kwargs):
    if not created:
        return None
    
    profile = getattr(instance.actor, 'playlistprofile', False)
    if profile:
        profile.points += 1
        profile.save()
signals.post_save.connect(new_follow, sender=models.get_model('actstream', 'Follow'))

def suggested_users_for(user):
    points = {}

    def count_points(user_list, points, value):
        for user in user_list:
            if user.pk not in points.keys():
                points[user.pk] = 0
            points[user.pk] += value

    exclude = Follow.objects.filter(user=user).values_list('object_id', flat=True)

    common_playlist = User.objects.filter(
        playlistprofile__fanof_playlists__in=user.playlistprofile.fanof_playlists.all()
    ).exclude(pk=user.pk).exclude(pk__in=exclude)
    count_points(common_playlist, points, 1)

    common_artists = User.objects.filter(
        playlistprofile__fanof_artists__in=user.playlistprofile.fanof_artists.all()
    ).exclude(pk=user.pk).exclude(pk__in=exclude)
    count_points(common_artists, points, 3)

    common_tiny = User.objects.filter(
        playlistprofile__tiny_playlist__tracks__in=
            user.playlistprofile.tiny_playlist.tracks.all()
    ).exclude(pk=user.pk).exclude(pk__in=exclude)
    count_points(common_artists, points, 4)

    sorted_points = sorted(points.iteritems(), key=operator.itemgetter(1))
    sorted_points.reverse()
    sorted_pks = [pk for pk, points in sorted_points][:3]
    users = User.objects.filter(pk__in=sorted_pks)
    sorted_users = sorted(users, key=lambda user: sorted_pks.index(user.pk))

    return sorted_users

def affinities_betwen(profile1, profile2):
    try:
        key1 = defaultfilters.slugify('%s and %s affinities' % (profile1.pk, profile2.pk))
        key2 = defaultfilters.slugify('%s and %s affinities' % (profile2.pk, profile1.pk))
    except AttributeError:
        return '?'

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

    if profile1_playlists_count == 0 \
        and profile1_artists_count == 0 \
        and profile1_tracks_count == 0:
        percent = 0

    #cache.set(key1, percent, 7200)
    #cache.set(key2, percent, 7200)

    return percent

class PlaylistProfile(models.Model):
    user = models.OneToOneField('auth.User', verbose_name=_(u'user'))
    user_location = models.CharField(max_length=100, verbose_name=_(u'location'), null=True, blank=True)
    tiny_playlist = models.ForeignKey('Playlist', related_name='favorite_of')
    fanof_playlists = models.ManyToManyField('playlist.Playlist', verbose_name=_(u'fav playlists'), null=True, blank=True, related_name='fans')
    fanof_artists = models.ManyToManyField('music.Artist', verbose_name=_(u'fav artists'), null=True, blank=True, related_name='fans')
    fanof_actions = models.ManyToManyField('actstream.Action', null=True, blank=True, related_name='fans')
    points = models.IntegerField(default=0)

    last_playlist = models.ForeignKey('playlist.Playlist', verbose_name=_(u'last playlist'), null=True, blank=True)
    avatar_url = models.TextField(null=True, blank=True, default='/site_media/static/images/avatar-logged.jpg')

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    def get_absolute_url(self):
        return urlresolvers.reverse('user_details', args=(self.user.username,))

    def follows(self):
        if not hasattr(self, '_follows'):
            self._follows = User.objects.filter(pk__in=Follow.objects.filter(user=self.user).values_list('object_id'))
        return self._follows

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
        except:
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
        return super(PlaylistManager, self).get_query_set().exclude(favorite_of__isnull=False)

    def all_with_hidden(self):
        return super(PlaylistManager, self).get_query_set()

class Playlist(models.Model):
    tracks = models.ManyToManyField('music.Track', verbose_name=_(u'tracks'), null=True, blank=True)
    category = models.ForeignKey(PlaylistCategory, verbose_name=_(u'category'), null=True, blank=True)
    play_counter = models.IntegerField(verbose_name=_(u'played'), default=0)
    
    creation_user = models.ForeignKey('auth.User', verbose_name=_(u'creator'))
    creation_datetime = models.DateTimeField(verbose_name=_(u'published'), auto_now_add=True)
    modification_datetime = models.DateField(verbose_name=_(u'modified'), auto_now=True)

    name = models.CharField(max_length=200, verbose_name=_(u'name'))
    slug = models.CharField(max_length=200, verbose_name=_(u'slug'))
    image = models.ImageField(verbose_name=_(u'icon'), null=True, blank=True, upload_to='playlist_images')
    tracks_count = models.IntegerField(default=0)
    fans_count = models.IntegerField(default=0)

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
                tracks = self.tracks.model.objects.filter(playlist=self).select_related().order_by('artist__name', 'name')

            for track in tracks:
                data['tracks'].append(track.to_dict(
                    with_artist=with_tracks_artist,
                    with_youtube_best_id=with_tracks_youtube_best_id
                ))

        if self.creation_user.username == 'radio':
            data['radio_artist'] = self.name
            data['object']['radioUrl'] = urlresolvers.reverse('radio_artist',
                args=(urllib.quote(self.name.encode('utf-8')),))

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
        ).select_related().order_by('artist__name', 'name').distinct()

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
            try:
                a = Playlist.tracks.field.rel.to.objects.get(pk=pk).artist
                a.last_playlist = instance
                a.save()
            except:
                pass
signals.m2m_changed.connect(last_playlist, sender=Playlist.tracks.through)
