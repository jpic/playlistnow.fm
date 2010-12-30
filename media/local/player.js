var player = {
    'ytplayer': false,
    'playTrack': function(track) {
        player.ytplayer.loadVideoById(track.youtube_best_id);
    
        $('.player_current_artist').html(track.artist.name);
        $('.player_current_artist').attr('href', track.artist.url);
        $('.player_current_track').html(track.name);
        $('.player_current_track').attr('href', track.url);
        $('.player_bttn_play').hide();
        $('.player_bttn_pause').show();
        $('.sidebar_Playing a').attr('href', track.url);
    },
    'playPlaylistTrack': function(index) {
        if (typeof index == 'object') {
            for(i in index) {
                if (this.playlist.tracks[index[i]] == undefined) {
                    continue;
                }
    
                this.currentTrackIndex = index[i];
                break;
            }
        } else {
            this.currentTrackIndex =  index;
        }
        
        this.playTrack(this.playlist.tracks[this.currentTrackIndex]);
    },
    'playPlaylist': function(url) {
        $.get(
            url,
            {
                'format': 'json',
            },
            function(data, textStatus, req) {
                player.playlist = data;
                if (!data.tracks.length) {
                    return true;
                }
                player.playPlaylistTrack(0);
            },
            'json'
        );
    },
    'playPrevious': function() {
        indexes = [
            player.currentTrackIndex - 1,
            player.playlist.tracks.length - 1,
        ];
        
        this.playPlaylistTrack(indexes);
    },
    'playNext': function() {
        indexes = [
            player.currentTrackIndex + 1,
            0,
        ];
        
        this.playPlaylistTrack(indexes);
    },
    'parseRenderedTrack': function(trackTag) {
        var hiddenTrackTag = trackTag.find('a.hidden.track');
        var hiddenYoutubeTag = trackTag.find('a.hidden.youtube_play');
        var hiddenArtistTag = trackTag.find('a.hidden.artist');

        track = {
            'name': hiddenTrackTag.html(),
            'url': hiddenTrackTag.attr('href'),
            'artist': {
                'name': hiddenArtistTag.html(),
                'url': hiddenArtistTag.attr('href'),
            },
            'youtube_best_id': hiddenYoutubeTag.attr('href'),
        }

        console.log(track);
    
        return track;
    },
    'parseRenderedPlaylist': function(playlistTag) {
        return {
            'name': $(this).html(),
            'url': $(this).attr('href'),
        }
    },
    'init': function() {
        $('li.song_play').live('click', function(e) {
            /* use when li.click != a.clikc */
            if( e.target != this ) {
                return true;
            }
            e.preventDefault();
            track = player.parseRenderedTrack($(this));
            player.playTrack(track);

            $('li.song_play').removeClass('selected');
            $(this).addClass('selected');
        });
        $('li.song_play span').live('click', function(e) {
            e.preventDefault();
            player.playTrack($(this).parent());
        $('li.song_play').removeClass('selected');
        li.addClass('selected');
        });
        $('.player_bttn_stop').click(function() { 
            player.ytplayer.stopVideo(); 
            $('.player_bttn_play').show();
            $('.player_bttn_pause').hide();
        });
        $('.player_bttn_pause').click(function() { 
            player.ytplayer.pauseVideo(); 
            $('.player_bttn_pause').hide();
            $('.player_bttn_play').show();
        });
        $('.player_bttn_play').click(function() { 
            player.ytplayer.playVideo(); 
            $('.player_bttn_play').hide();
            $('.player_bttn_pause').show();
        });
        $('.player_bttn_mute').click(function() {
            player.ytplayer.mute();
        });
        $('.player_bttn_forw').click(function(e) {
            e.preventDefault();
            player.playNext()
        });
        $('.player_bttn_prev').click(function(e) {
            e.preventDefault();
            player.playPrevious();
        });
        $('div.playlist').live('click', function(e) {
            e.preventDefault();
            var url = $(this).find('a').attr('href');
            player.playPlaylist(url);
        });
    }
}

$(document).ready(function() {
    player.init();
});
