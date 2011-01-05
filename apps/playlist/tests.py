import unittest
       
from playlist.models import *
from music.models import *
from django.contrib.auth.models import User

class PlaylistModificationTestCase(unittest.TestCase):
    def setUp(self):
        # music fixtures
        self.a0 = Artist(name='fooman')
        self.a0.save()
        self.t0 = Track(artist=self.a0, name='t0', youtube_id='aeu')
        self.t0.save()
        self.t1 = Track(artist=self.a0, name='t1', youtube_id='aeu')
        self.t1.save()
        self.t2 = Track(artist=self.a0, name='t2', youtube_id='aeu')
        self.t2.save()

        # user fixtures
        self.u0=User(username='u0')
        self.u0.save()
        self.u1=User(username='u1')
        self.u1.save()
        self.u2=User(username='u2')
        self.u2.save()

        # playlist fixtures
        self.p0=Playlist(creation_user=self.u0, name='p0')
        self.p0.save()
        self.p0.tracks.add(self.t0)

    def assertListEquals(self, result, expected):
        return self.assertEqual(list(result), list(expected))

    def testAllUserTracks(self):
        # assert that all users see all tracks before any modification is saved
        self.assertListEquals(
            self.p0.all_user_tracks(self.u0),
            self.p0.tracks.all()
        )
        self.assertListEquals(
            self.p0.all_user_tracks(self.u1),
            self.p0.tracks.all()
        )
        self.assertListEquals(
            self.p0.all_user_tracks(self.u2),
            self.p0.tracks.all()
        )

        # if u1 adds t1 to p0, then u1 should have 2 tracks but u0 should
        # still have only the one he added
        PlaylistModification(
            playlist=self.p0, 
            creation_user=self.u1, 
            track=self.t1,
            action='add'
        ).save()

        # assert that u0 sees *only* his tracks
        self.assertListEquals(
            self.p0.all_user_tracks(self.u0),
            [self.t0]
        )

        # assert that t1 was not added for other users
        self.assertListEquals(
            self.p0.all_user_tracks(self.u0),
            [self.t0]
        )

        # assert that u1 sees all tracks
        self.assertListEquals(
            self.p0.all_user_tracks(self.u1),
            [self.t1, self.t0]
        )

        # test an "rm" modification
        PlaylistModification(
            playlist=self.p0, 
            creation_user=self.u1, 
            track=self.t0,
            action='rm'
        ).save()

        # assert that u0 sees *only* his tracks
        self.assertListEquals(
            self.p0.all_user_tracks(self.u0),
            [self.t0]
        )

        # assert that t1 was not added for other users
        self.assertListEquals(
            self.p0.all_user_tracks(self.u2),
            [self.t0]
        )

        # assert that u1 does not see removed t0
        self.assertListEquals(
            self.p0.all_user_tracks(self.u1),
            [self.t1]
        )

        # assert that modifications by u2 only affects him
        # this part just strengthen the past assertions
        # using a third user
        PlaylistModification(
            playlist=self.p0, 
            creation_user=self.u2,
            track=self.t2,
            action='add'
        ).save()
        self.assertListEquals(
            self.p0.all_user_tracks(self.u0),
            [self.t0]
        )
        self.assertListEquals(
            self.p0.all_user_tracks(self.u1),
            [self.t1]
        )
        self.assertListEquals(
            self.p0.all_user_tracks(self.u2),
            [self.t0,self.t2]
        )
