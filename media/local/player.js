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
        $('.player_current_playlist').hide();

        this.track_history.push(track);
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

        var currentPlaylist = $('.player_current_playlist');
        currentPlaylist.html('- I am ' + this.playlist['object']['name']);
        currentPlaylist.attr('href', this.playlist['object']['url']);
        currentPlaylist.fadeIn();
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
        var track = this.track_history.pop().pop();
        if (track) {
            this.playTrack(track);
        } else {
            indexes = [
                player.currentTrackIndex - 1,
                player.playlist.tracks.length - 1,
            ];
            
            this.playPlaylistTrack(indexes);
        }
    },
    'playNext': function() {
        indexes = [
            player.currentTrackIndex + 1,
            0,
        ];

        do {
            index = Math.floor(Math.random()*(player.playlist.tracks.length + 1))
        } while (index == player.currentTrackIndex)
        
        this.playPlaylistTrack(index);
    },
    'parseRenderedTrack': function(trackTag) {
        var hiddenTrackTag = trackTag.find('a.track');
        var hiddenYoutubeTag = trackTag.find('a.youtube_play');
        var hiddenArtistTag = trackTag.find('a.artist');

        track = {
            'name': hiddenTrackTag.html(),
            'url': hiddenTrackTag.attr('href'),
            'artist': {
                'name': hiddenArtistTag.html(),
                'url': hiddenArtistTag.attr('href'),
            },
            'youtube_best_id': hiddenYoutubeTag.attr('href'),
        }

        return track;
    },
    'parseRenderedPlaylist': function(playlistTag) {
        return {
            'name': $(this).html(),
            'url': $(this).attr('href'),
        }
    },
    'init': function() {
        this.track_history = [];
        
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
        $('li.song_play .play').live('click', function(e) {
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
        $('div.playlist, div.playlist .play').live('click', function(e) {
            if( e.target != this ) {
                return true;
            }

            e.preventDefault();

            var url = $(this).find('a').attr('href');
            if (!url) {
                url = $(this).parents('div.playlist').find('a').attr('href');
            }
            player.playPlaylist(url);
        });
        $('.song_play .remove').live('click', function(e) {
            e.preventDefault();
            var track = player.parseRenderedTrack($(this).parent());
            var playlist = false;
            $(document).trigger('signalPlaylistTrackModificationRequest', [track, playlist, 'remove'])
        });
        $('.song_play .add').live('click', function(e) {
            e.preventDefault();
            var track = player.parseRenderedTrack($(this).parent());
            var playlist = false;
            if ($('#playlist_pk').length > 0) {
                playlist = {
                    'pk': $('#playlist_pk').html(),
                };
            }
            $(document).trigger('signalPlaylistTrackModificationRequest', [track, playlist, 'add'])
        });
    }
}

$(document).ready(function() {
    player.init();
});
