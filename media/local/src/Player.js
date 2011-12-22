var Player = (function() {
    $('.do_add_current_track').click(function(e) {
    });
    $('.do_share_current_track').click(function(e) {
    });
    $('li.song_play').live('click', function(e) {
        /* use when li.click != a.clikc */
        if( e.target != this ) {
            return true;
        }
        track = Player.parseRenderedTrack($(this));
        // get track's playlist
    });

    function playTrack(track) {
    }
    function queueTracks(tracks) {
    }

    return {
        queue: [],
        history: [],
        play: function(arg) {
            // just interrupts the current track and play this
            // if track
            playTrack(arg);

            // if url
            playlist = Model.fetchPlaylist(arg);
            // else
            playlist = arg

            playTrack(playlist.tracks[0]);
            queueTracks(playlist.tracks[
        },
        queue: function(arg) {
            // just interrupts the current track and queue this
            // if track
            queueTrack(arg);
            // if queuelist
            queuePlaylist(arg);
            // if url
            queuePlaylist(Model.fetchPlaylist(arg));
        },
    }
})();
