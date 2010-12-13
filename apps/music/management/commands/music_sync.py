import logging
from lxml import etree

from django.core.management.base import NoArgsCommand
from django.conf import settings

from music.models import *

etree.set_default_parser(etree.XMLParser(no_network=False))

letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
letters = ['a']

class Command(NoArgsCommand):
    help = "Synchronise lastfm artist, track and album database."
   
    def handle_noargs(self, **options):
        logging.basicConfig(level=logging.DEBUG, format="%(message)s")
        logging.info("-" * 72)

        for letter in letters:
            total_pages = None

            url = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&method=%s&artist=%s&page=%s' % (
                settings.LASTFM_API_KEY,
                'artist.search',
                letter,
                1
            )

            tree = etree.parse(url)
            for item in tree.iter():
                if not total_pages and 'totalResults' in item.tag:
                    # +2 was required as of 2010-12-10
                    total_pages = ( int(item.text) / 30 ) + 2

            page = 1464
            artist = {}
            while page <= total_pages:
                logging.info("Doing page %s of search term '%s'" % (page, letter))

                url = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&method=%s&artist=%s&page=%s' % (
                    settings.LASTFM_API_KEY,
                    'artist.search',
                    letter,
                    page
                )

                try:
                    tree = etree.parse(url)
                except Exception:
                    page += 1
                    logging.warn("Broken page: %s" % url)
                    continue

                for item in tree.iter():
                    if item.tag == 'name':
                        # save the current artist and create a new one
                        if artist:
                            model, created = Artist.objects.get_or_create(name=artist['name'])
                            model.lastfm_listeners = artist['lastfm_listeners']
                            model.lastfm_mbid = artist['lastfm_mbid']
                            model.save()
                        
                        artist = {
                            'name': item.text
                        }
                    
                    elif item.tag == 'streamable' and item.text == '0':
                        # usually non streamable artist aren't interresting for
                        # our database
                        artist = None
                        continue

                    elif item.tag == 'listeners' and not item.text:
                        # usually artists with less than 100 aren't interresting
                        # for our database
                        artist = None
                        continue

                    elif item.tag == 'listeners':
                        artist['lastfm_listeners'] = int(item.text)

                    elif item.tag == 'mbid' and not item.text:
                        # usually artists without uuid aren't interresting for 
                        # our database
                        artist = None
                        continue

                    elif item.tag == 'mbid':
                        artist['lastfm_mbid'] = item.text

                if artist:
                    model, created = Artist.objects.get_or_create(name=artist['name'])
                    model.lastfm_listeners = artist['lastfm_listeners']
                    model.lastfm_mbid = artist['lastfm_mbid']
                    model.save()

                page += 1
