describe('Artist', function() {
    it('has properties', function() {
        var subject = new Artist();
        expect(subject.url).toEqual('');
        expect(subject.name).toEqual('');
        expect(subject.thumbnail).toEqual('');
    });

    it('has a constructor', function() {
        var subject = new Artist({
            name: 'Foo',
            url: 'http://example.com',
            thumbnail: 'http://example.com/2.gif',
        });
        expect(subject.name).toEqual('Foo');
        expect(subject.url).toEqual('http://example.com');
        expect(subject.thumbnail).toEqual('http://example.com/2.gif');
    });
});

