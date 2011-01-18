from django.core.management.base import BaseCommand, CommandError
from django import db
from django.db import connection, transaction

from music.models import Artist

class Command(BaseCommand):
    def handle(self, *args, **options):
        cursor = connection.cursor()
        cursor.execute('''
        select 
            artist_id,
            count(*)
        from
            playlist_playlistprofile_fanof_artists
        group by artist_id
        order by count desc
        ''')
        i = 1
        for row in cursor.fetchall():
            Artist.objects.filter(pk=row[0]).update(rank=i)
            i+=1
