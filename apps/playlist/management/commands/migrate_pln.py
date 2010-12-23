import datetime

from django.core.management.base import BaseCommand, CommandError
from django import db
from django.contrib.auth.models import User

from playlist.models import *

class Command(BaseCommand):
    args = 'n/a'
    help = 'imports dataset from previous structure'

    def handle(self, *args, **options):
        backend = db.load_backend('mysql')
        conn = backend.DatabaseWrapper({'NAME': 'pln', 'USER': 'root', 'PASSWORD': '', 'HOST': 'localhost', 'PORT': '3306', 'OPTIONS': ''})
        old = conn.cursor()

        #self.sync_users(old)
        self.sync_playlists(old)
    
    def sync_users(self, old):
        raise NotImplemented
        old.execute('select id, name, "jamespic@gmail.com" from users')
        for old_user in old.fetchall()

    def sync_playlists(self, old):
        old.execute('select id, name, played, published from playlists')
        for old_playlist in old.fetchall():
            try:
                playlist = Playlist.objects.get(id=old_playlist[0])
            except Playlist.DoesNotExist:
                playlist = Playlist(id=old_playlist[0])

            playlist.name = old_playlist[1]
            playlist.play_counter = old_playlist[2]
            playlist.creation_datetime = old_playlist[3] or datetime.datetime.now()
            playlist.creation_user = User.objects.get(pk=1)
            playlist.save()
