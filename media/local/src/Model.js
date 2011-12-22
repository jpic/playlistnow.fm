var Model = (function() {
    function ajax(kwargs) {
    }
    function makeTrackPlaylistData(track, playlist) {
        if (track && playlist) {
            data['direct_to_playlist'] = true;
        }
    }

    return {
        state: {
            messages: [],
            tiny: new Playlist(),
            url: '',
        },
        addTrackToPlaylist: function(track, playlist) {
            data = makeTrackPlaylistData(track, playlist);
            data['action'] = 'add';
            ajax({
                url: Django.getUrl('playlist_track_modify'),
                type: 'post',
            });
        },
        removeTrackFromPlaylist: function(track, playlist) {
            data = makeTrackPlaylistData(track, playlist);
            data['action'] = 'remove';
            ajax({
                url: Django.getUrl('playlist_track_modify'),
                type: 'post',
            });
        },
        fetchPlaylist: function(url) {
        },
        getState: function() {
            return this.state;
        },
    }
})();
