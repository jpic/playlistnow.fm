import sys
import datetime

from django.core.management.base import BaseCommand, CommandError
from django import db
from django.contrib.auth.models import User

from jpic.slughifi import slughifi
from jpic.progressbar import ProgressBar

from playlist.models import *

class Command(BaseCommand):
    args = 'n/a'
    help = 'imports dataset from previous structure'

    def handle(self, *args, **options):
        backend = db.load_backend('mysql')
        conn = backend.DatabaseWrapper({'NAME': 'pln', 'USER': 'root', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': '3306', 'OPTIONS': ''})
        old = conn.cursor()

        #self.sync_users(old)
        self.sync_categories(old)
        self.sync_playlists(old)

    def count_table(self, old, table):
        old.execute('select count(*) from %s' % table)
        result = old.fetchone()
        return result[0]

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

    def sync_users(self, old):
        print "Migrating users ..."
        prog = ProgressBar(0, self.count_table(old, 'users'), 77, mode='fixed')

        old.execute('select id, name, email from users u left join users_emails ue on ue.userId = u.id')
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
            user.save()
            
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
            playlist.creation_datetime = old_playlist[3] or datetime.datetime.now()
            try:
                playlist.creation_user = User.objects.get(pk=old_playlist[4])
            except User.DoesNotExist:
                # assign orphin playlists to root
                playlist.creation_user = User.objects.get(pk=1)

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
    t.name 
from playlists_tags pt
left join tags t on t.id = pt.tagId 
where
pt.playlistId = %s
''' % int(playlist.pk))
            playlist.tags = ','.join([i[0] for i in old.fetchall()])
            playlist.save()

            prog.increment_amount()
            print prog, '\r',
            sys.stdout.flush()
