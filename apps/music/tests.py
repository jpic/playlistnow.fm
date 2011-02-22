import unittest

from models import *

class GetOrFakeTrackTestCase(unittest.TestCase):
    def testNewTrackNoArtist(self):
        """
        In this website version, tracks are not saveable without artist
        """
        pass

    def testNewTrackNewArtist(self):
        """
        The artist is not in the database in this case (nor is the track)
        """
        track = get_or_fake_track('rock this town', 'stray cats')
        # assert name was auto corrected
        self.assertEqual(track.name, 'Rock This Town')
        self.assertEqual(track.artist.name, 'Stray Cats')
        # assert new track and artist where not saved
        self.assertEqual(track.pk, None)
        self.assertEqual(track.artist.pk, None)

    def testNewTrackExistingArtist(self):
        """
        Another track exist for this artist, so the artist should be fetched.
        """
        a = Artist(name='Canned Heat')
        a.lastfm_get_info()
        a.save()

        track = get_or_fake_track('on the road again', 'canned heat')
        # assert name was auto corrected by last.fm
        self.assertEqual(track.name, 'On The Road Again')
        self.assertEqual(track.pk, None)
        # assert that artist was found
        self.assertEqual(track.artist.name, a.name)
        self.assertEqual(track.artist.pk, a.pk)

    def testExistingTrackNoArtist(self):
        """
        A track that exists from older versions of the website.
        """
        artist = Artist(name='YouTube')
        artist.save()
        t = Track(name='Run On - Blind Boys of Alabama', artist=artist)
        t.save()

        track = get_or_fake_track('Run On - Blind Boys of Alabama')
        # assert track was found
        self.assertEqual(track.name, t.name)
        self.assertEqual(track.pk, t.pk)
        # assert artist is youtube
        self.assertEqual(track.artist.name, t.artist.name)
        self.assertEqual(track.artist.pk, t.artist.pk)
    
    def testExistingTrackExistingArtist(self):
        """
        This track already exists in the database (so does the artist)
        """
        artist = Artist(name='The Jon Spencer Blues Explosion')
        artist.save()
        t = Track(name='afro', artist=artist)
        t.save()

        track = get_or_fake_track('afro', 'the jon spencer blues explosion')
        # assert track was found
        self.assertEqual(track.name, t.name)
        self.assertEqual(track.pk, t.pk)
        # assert artist was found
        self.assertEqual(track.artist.name, t.artist.name)
        self.assertEqual(track.artist.pk, t.artist.pk)

class SaveIfFakeTrackTestCase(unittest.TestCase):
    def testNewTrackNewArtist(self):
        """
        The artist is not in the database in this case (nor is the track)
        """
        track = Track(name='rock this town', artist=Artist(name='stray cats'))
        save_if_fake_track(track)

        # assert track and artist where both saved ...
        self.assertNotEqual(track.pk, None)
        self.assertNotEqual(track.artist.pk, None)
        # ... correctly
        self.assertEqual(track.artist, Artist.objects.get(pk=track.artist.pk))
        self.assertEqual(track, Track.objects.get(pk=track.pk))

    def testNewTrackExistingArtist(self):
        """
        Another track exist for this artist, so the artist should be fetched.
        """
        a = Artist.objects.get(name='Canned Heat')

        track = Track(name='on the road again', artist=a)
        save_if_fake_track(track)
        # assert that the track was saved ...
        self.assertNotEqual(track.pk, None)
        # ... correctly
        self.assertEqual(track, Track.objects.get(pk=track.pk))
        # (double) assert that the artist was reused
        self.assertEqual(a.pk, track.artist.pk)
        self.assertEqual(a, track.artist)
