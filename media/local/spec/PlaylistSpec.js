describe('Playlist', function() {
    var playlist, track0, track1;
    
    beforeEach(function() {
        playlist= new Playlist();
        track0 = new Track({name: 'track0 name'});
        track1 = new Track({name: 'track1 name'});
    });

    it('has properties', function() {
        expect(playlist.tracks).toEqual([]);
        expect(playlist.pk).toEqual(null);
        expect(playlist.name).toEqual('');
        expect(playlist.url).toEqual('');
    });

    it('has a constructor', function() {
        var subject = new Playlist({
            tracks: [ track0, track1 ],
            pk: 5,
            name: 'Foo',
            url: 'http://example.com',
        });
        expect(subject.tracks).toEqual([track0, track1]);
        expect(subject.pk).toEqual(5);
        expect(subject.name).toEqual('Foo');
        expect(subject.url).toEqual('http://example.com');
    });

    it('can add tracks', function() {
        playlist.add(track0);
        expect(playlist.tracks).toEqual([track0]);

        playlist.add(track1);
        expect(playlist.tracks).toEqual([track0, track1]);
    });

    it('can remove tracks', function() {
        playlist.add(track0);
        playlist.add(track1);

        playlist.remove(track0);
        expect(playlist.tracks).toEqual([track1]);

        playlist.remove(track1);
        expect(playlist.tracks).toEqual([]);
    });
});
