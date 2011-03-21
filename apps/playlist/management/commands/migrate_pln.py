import sys
import datetime

from django.core.management.base import BaseCommand, CommandError
from django import db
from django.contrib.auth.models import User
from actstream.models import follow

from jpic.slughifi import slughifi
from jpic.progressbar import ProgressBar

from playlist.models import *
from music.models import *
from gfc.models import *
from socialregistration.models import *

class Command(BaseCommand):
    args = 'n/a'
    help = 'imports dataset from previous structure'

    def handle(self, *args, **options):
        backend = db.load_backend('mysql')
        conn = backend.DatabaseWrapper({'NAME': 'pln', 'USER': 'root', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': '3306', 'OPTIONS': ''})
        old = conn.cursor()

        self.sync_users_accounts(old)
        #self.sync_followers(old)
        #self.sync_categories(old)
        #self.sync_tracks(old)
        #self.sync_playlists(old)
        #self.sync_tiny_playlist(old)
        #self.sync_artists(old)

    def count_table(self, old, table):
        old.execute('select count(*) from %s' % table)
        result = old.fetchone()
        return result[0]

    def sync_followers(self, old):
        print "Migrating followers ..."
        prog = ProgressBar(0, self.count_table(old, 'users_followers'), 77, mode='fixed')

        old.execute('select * from users_followers')
        for old_follower in old.fetchall():
            if not old_follower[0]: continue
            if not old_follower[1]: continue

            try:
                user = User.objects.get(pk=old_follower[0])
                follower = User.objects.get(pk=old_follower[1])
                follow(follower, user, False)
            except:
                continue

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()


    def sync_categories(self, old):
        print "Migrating categories ..."
        prog = ProgressBar(0, self.count_table(old, 'categories'), 77, mode='fixed')

        old.execute('select * from categories order by parent')
        for old_category in old.fetchall():
            category, created = PlaylistCategory.objects.get_or_create(
                pk=old_category[0])
            category.name = old_category[4]
            category.save()
            if old_category[2]:
                category.parent, pcreated = PlaylistCategory.objects.get_or_create(
                    pk=old_category[2])
                category.parent.save()
                category.save()

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()

    def sync_users_accounts(self, old):
        print "Migrating users accounts ..."
        prog = ProgressBar(0, self.count_table(old, 'users'), 77, mode='fixed')

        old.execute('''
            select 
                u.id, 
                u.name,
                ue.email,
                ua.accountLocation,
                ua.accountAvatar,
                up.pts
            from users u 
            left join users_emails ue on ue.userId = u.id
            left join users_accounts ua on ua.userId = u.id
            left join users_pts up on up.idUser = u.id
        ''')
        for old_user in old.fetchall():
            # skipping the couple of nonames
            if not old_user[1]: continue

            user, created = User.objects.get_or_create(pk=old_user[0])
            count = 0
            user.username = slughifi(old_user[1])[:30] or count
            while User.objects.filter(username=user.username).exclude(pk=user.pk).count():
                user.username = '%s%s' % (slughifi(old_user[1])[:28], count)
                count += 1
            user.email = old_user[2] or 'no@email.com'
            user.first_name = old_user[1]
            user.save()

            user.playlistprofile.points = old_user[5]
            if old_user[3]:
                user.playlistprofile.user_location = old_user[3]
            if old_user[4]:
                user.playlistprofile.avatar_url = old_user[4]
            user.playlistprofile.save()
           
            old.execute('select * from users_accounts where userId = ' + str(old_user[0]))
            for old_account in old.fetchall():
                if old_account[1] == 'FACEBOOK':
                    p, created=FacebookProfile.objects.get_or_create(uid=old_account[2], user=user)
                    p.save()
                
                elif old_account[1] == 'TWITTER':
                    p, created=TwitterProfile.objects.get_or_create(twitter_id=old_account[2],user=user)
                    p.save()
                
                elif old_account[1] == 'GOOGLE':
                    p, created=GfcProfile.objects.get_or_create(uid=old_account[2],user=user)
                    p.save()   

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()

    def sync_tiny_playlist(self,old):
        print "Migrating tiny playlist ..."
        prog = ProgressBar(0, self.count_table(old, 'users_likedSongs'), 77, mode='fixed')

        old.execute('select * from users_likedSongs')
        for old_liked in old.fetchall():
            try:
                user = User.objects.get(pk=old_liked[0])
                track = Track.objects.get(pk=old_liked[1])
                user.playlistprofile.tiny_playlist.tracks.add(track)

                # todo: user old_liked[2] timestamp to correct the action

                prog.increment_amount()
                print prog, '\r',
                sys.stdout.flush()
            except:
                pass

    def sync_users_fans(self,old):
        print "Migrating users activities ..."
        prog = ProgressBar(0, self.count_table(old, 'users'), 77, mode='fixed')

        old.execute('select * from users_activities where type=9')
        for old_activity in old.fetchall():
            user = User.objects.get(pk=old_activity[1])

            if old_activity[5] == 9:
                artist = Artist.objects.get(pk=old_activity[6])
                artist.fans.add(user.playlistprofile)
            else:
                print 'fail'

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()

    def sync_artists(self, old):
        print "Migrating artists ..."
        prog = ProgressBar(0, self.count_table(old, 'artists_fans'), 77, mode='fixed')

        old.execute('select userId, artistId, name from artists_fans af left join artists a on a.id = af.artistId')
        for old_activity in old.fetchall():
            # skip empty artist names
            if not old_activity[2]: continue

            artist, created = Artist.objects.get_or_create(pk=old_activity[1], name=old_activity[2])
            if created or not artist.image_small:
                # set the name for lastfm to find
                artist.name = old_activity[2]
                artist.lastfm_get_info()
                # override the lastfm corrected name in favor of pln validated
                # name
                artist.name = old_activity[2]
                artist.save()
            
            try:
                user = User.objects.get(pk=old_activity[0])
            except User.DoesNotExist:
                continue
            
            artist.fans.add(user.playlistprofile)

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()

    def sync_playlists(self, old):
        print "Migrating playlists ..."
        prog = ProgressBar(0, self.count_table(old, 'playlists'), 77, mode='fixed')

        old.execute('select id, name, played, published, createdBy from playlists')
        for old_playlist in old.fetchall():
            try:
                playlist = Playlist.objects.get(id=old_playlist[0])
            except Playlist.DoesNotExist:
                playlist = Playlist(id=old_playlist[0])

            playlist.name = old_playlist[1]
            playlist.play_counter = old_playlist[2]
            playlist.creation_datetime = old_playlist[3] or datetime.now()
            try:
                playlist.creation_user = User.objects.get(pk=old_playlist[4])
            except User.DoesNotExist:
                # assign orphin playlists to root
                playlist.creation_user = User.objects.get(username='root')

            old.execute('''
select 
    pc.categoryId
from playlists_categories pc
where
    pc.playlistId = %s
''' % int(playlist.pk))

            for old_cat in old.fetchall():
                # skipping more dead relations weee
                if not old_cat[0]:
                    continue
                playlist.category = PlaylistCategory.objects.get(pk=old_cat[0])

            playlist.save()

            old.execute('''
select 
    userId 
from users_bookmarkedPlaylists
where
    playlistId = %s
''' % int(playlist.pk))

            for old_fan in old.fetchall():
                # skipping more dead relations weee
                if not old_fan[0]: continue

                try:
                    fan = User.objects.get(pk=old_fan[0])
                    playlist.fans.add(fan.playlistprofile)
                except:
                    pass

            old.execute('''
select 
    t.name 
from playlists_tags pt
left join tags t on t.id = pt.tagId 
where
pt.playlistId = %s
''' % int(playlist.pk))
            playlist.tags = ','.join([i[0] for i in old.fetchall()])
            playlist.save()


            old.execute('select songId from playlists_songs where playlistId = %s' % int(playlist.pk))
            for old_song in old.fetchall():
                # skipping more dead relations weee
                if not old_song[0]:
                    continue
                playlist.tracks.add(Track.objects.get(pk=old_song[0]))

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()


    def sync_tracks(self, old):
        print "Migrating tracks ..."
        prog = ProgressBar(0, self.count_table(old, 'songs'), 77, mode='fixed')

        old.execute('''
select
    s.id,
    s.title, 
    s.played, 
    ys.youtubeId, 
    a.id as artist_id,
    a.name,
    ys.bugs
from songs s 
left join youtubeSongs ys on ys.songId = s.id 
left join artists a on a.id = s.artistId
        ''')
        for old_track in old.fetchall():
            artist, created = Artist.objects.get_or_create(pk=old_track[4])
            artist.name = old_track[5]
            artist.save()

            try:
                track = Track.objects.get(pk=old_track[0])
            except Track.DoesNotExist:
                track = Track(pk=old_track[0])

            track.name = old_track[1]
            track.play_counter = old_track[2]
            track.youtube_id = old_track[3]
            track.youtube_bugs = old_track[6]
            track.artist = artist

            track.save()

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()
