import logging

import lastfm

from django.core.management.base import NoArgsCommand

from music.models import *
from music.views import get_lastfm_api

letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
letters = ['a']

class Command(NoArgsCommand):
    help = "Synchronise lastfm artist, track and album database."
   
    def handle_noargs(self, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logging.info("-" * 72)
        api = get_lastfm_api()

        for letter in letters:
            logging.debug("Loop for letter %s" % letter)

            page = 1
            count = None

            while count == None or count > 30:
                logging.debug("  Loop for page %s" % page)
                
                count = 0
                page += 1
                
                artists = lastfm.Artist.search(api, letter, page=page)
                
                try:
                    for artist in artists:
                        self.save_artist(artist)
                        count += 1
                except lastfm.LastfmError:
                    """
                    An operationnal error is sometimes raised because the xml
                    is "malformed", but iterating over the list again works in
                    that case ...
                    """
                    for artist in artists:
                        self.save_artist(artist)
                        count += 1
                
                logging.debug("  Got %s" % count)
    
    def save_artist(self, artist):
        if not artist.streamable:
            return True

        model = Artist()
        model.name = artist.name
        model.lastfm_listeners = artist.listeners
        model.lastfm_mbid = artist.mbid
        model.lastfm_url = artist.url

        model.save()
