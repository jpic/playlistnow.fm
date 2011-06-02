describe('Track', function() {
    it('has properties', function() {
        var subject = new Track();
        expect(subject.artist).toEqual(new Artist());
        expect(subject.name).toEqual('');
        expect(subject.url).toEqual('');
        expect(subject.youtube_id).toEqual('');
    });

    it('has a constructor', function() {
        var subject = new Track({
            name: 'Foo',
            youtube_id: 'YooFoo',
            artist: new Artist({
                name: 'Yoo',
            }),
            url: 'http://example.com',
        });
        expect(subject.name).toEqual('Foo');
        expect(subject.artist).toEqual(new Artist({name: 'Yoo'}));
        expect(subject.artist.name).toEqual('Yoo');
        expect(subject.youtube_id).toEqual('YooFoo');
        expect(subject.url).toEqual('http://example.com');
    });
});

