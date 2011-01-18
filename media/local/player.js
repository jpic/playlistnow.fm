function getPercent(all, part)
{
    return (all > 0) ? (100 / all) * part : 0;
}

var player = {
    'ytplayer': false,
    'tiny_playlist': {},
    'playTrack': function(track, playlist, fromHistory /* new in history ? (bool) */) {
        player.ytplayer.loadVideoById(track.youtube_best_id);
        this.state.currentTrack = track;
        this.hiliteCurrentTrack(); 

        $('.player_current_artist').html(track.artist.name);
        $('.player_current_artist').attr('href', track.artist.url);
        $('.player_current_track').html(track.name + ' - ');
        $('.player_current_track').attr('href', track.url);
        $('.player_bttn_play').hide();
        $('.player_bttn_pause').show();
        $('.sidebar_Playing a').attr('href', track.url);
        $('.player_current_playlist').hide();

        if (!fromHistory) {
            this.state.trackHistory.push(track);
            this.state.currentTrackHistoryIndex = this.state.trackHistory.length - 1;
        }
    },
    'playPlaylistTrack': function(index, fromHistory) {
        if (typeof index == 'object') {
            for(i in index) {
                if (this.state.currentPlaylist.tracks[index[i]] == undefined) {
                    continue;
                }
    
                this.state.currentPlaylistTrackIndex = index[i];
                break;
            }
        } else if (typeof index == 'number' && 
            this.state.currentPlaylist.tracks[index]) {
            this.state.currentPlaylistTrackIndex = index;
        } else {
            this.state.currentPlaylistTrackIndex = 0;
        }
        
        var track = this.state.currentPlaylist.tracks[this.state.currentPlaylistTrackIndex]
        track.playlist = this.state.currentPlaylist;
        track.playlistTrackIndex = this.state.currentPlaylistTrackIndex;

        if (track == undefined) {
            return true;
        }

        this.playTrack(track, this.state.currentPlaylist, fromHistory);

        var currentPlaylist = $('.player_current_playlist');

        if (this.state.currentPlaylist['object']['name']) {
            currentPlaylist.html(
                track.playlist['object']['name']
            );
            currentPlaylist.attr(
                'href',
                track.playlist['object']['url']
            );
            currentPlaylist.show();
        } else {
            currentPlaylist.hide();
        }
    },
    'playPlaylist': function(playlist, offset) {
        if (typeof playlist == 'object') {
            player.state.currentPlaylist = playlist;
            if (player.state.currentPlaylist.tracks.length) {
                player.playPlaylistTrack(offset);
            }
        } else {
            $.get(
                playlist,
                {
                    'format': 'json',
                },
                function(data, textStatus, req) {
                    player.state.currentPlaylist = data;
                    if (player.state.currentPlaylist.tracks.length) {
                        player.playPlaylistTrack(offset);
                    }
                },
                'json'
            );
        }
    },
    'playPrevious': function() {
        if (player.state.currentTrackHistoryIndex <= 0) {
            return true;
        }

        var track = player.state.trackHistory[player.state.currentTrackHistoryIndex-1];
        
        if (track) {
            player.state.currentTrackHistoryIndex -= 1;
            player.playTrack(track, false, true);
        } else {
            return true;
        }
    },
    'playNext': function() {
        if (player.state.repeatMode && player.state.trackHistory.length >= 1) {
            player.playTrack(player.state.trackHistory[player.state.currentTrackHistoryIndex], false, true);
        } else if (player.state.currentPlaylist && player.state.currentTrackHistoryIndex == player.state.trackHistory.length - 1) {
            /* if nothing pending in history: */
            /* if only one track in playlist: plain fail */
            if (player.state.currentPlaylist.tracks.length <= 1) {
                player.playPlaylistTrack(player.state.currentPlaylistTrackIndex, true);
            }
            /* else use playlist */
            else if (player.state.randomMode) {
                do {
                    var index = Math.floor(
                        Math.random()*(player.state.currentPlaylist.tracks.length)
                    )
                } while (index == player.state.currentPlaylistTrackIndex)
                player.playPlaylistTrack(index);
            } else {
                var nextIndex = player.state.currentPlaylistTrackIndex + 1;
                if (player.state.currentPlaylist.tracks[nextIndex] != undefined) {
                    player.playPlaylistTrack(nextIndex);
                } else {
                    player.playPlaylistTrack(0);
                }
            }
        } else {
            if(player.state.trackHistory[player.state.currentTrackHistoryIndex+1]) {
                player.state.currentTrackHistoryIndex += 1;
                player.playTrack(player.state.trackHistory[player.state.currentTrackHistoryIndex], false, true);
            } else {
                player.state.currentTrackHistoryIndex = 0;
                player.playTrack(player.state.trackHistory[0], false, true);
            }
        }

        return true;
    },
    'parseTrackList': function(ul) {
        var playlist = {
            'object': {},
            'tracks': [],
        };

        ul.find('li.song_info').each(function() {
            var track = player.parseRenderedTrack($(this));
            track.playlist = playlist;
            playlist.tracks.push(track);
        });

        return playlist;
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
            'li': trackTag,
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
        this.state = {
            'randomMode': true,
            'repeatMode': false,
            'trackHistory': [],
            'currentPlaylist': false,
            'currentPlaylistTrackIndex': 0,
            'currentTrackHistoryIndex': 0,
        }
        this.initBinds();
    },
    'hiliteFavoriteTracks': function() {
        if (player.tiny_playlist.tracks == undefined) {
            return true;
        }

        for(var i in player.tiny_playlist.tracks) {
            var track = player.tiny_playlist.tracks[i];

            $('li.song_info.external_track a.track[href=' + track.url + ']').each(function() {
                var icon = $(this).parent().find('.icon.tiny_playlist');
                icon.css(
                    'backgroundPosition',
                    'left bottom'
                );
                icon.addClass('remove_track');
                icon.removeClass('add_track');
            });
        }
    },
    'hiliteCurrentTrack': function() {
        if (player.state.currentTrack == undefined) {
            return true;
        }

        $('li.song_info.selected').removeClass('selected');
        $('li.song_info a.track[href=' + player.state.currentTrack.url + ']').each(function() {
            $(this).parent().addClass('selected');
        });
    },
    'initBinds': function() {
        $(document).bind('signalPageUpdate', function() {
            player.hiliteCurrentTrack();
            player.hiliteFavoriteTracks();
        });
        $(document).bind('signalPlaylistUpdate', function(e, playlist_pk) {
            if(!player.state.currentPlaylist) {
                return true;
            }
            if(playlist_pk == player.state.currentPlaylist.object.pk) {
                $.get(
                    player.state.currentPlaylist.object.url,
                    {
                        'format': 'json',
                    },
                    function(data, textStatus, req) {
                        player.state.currentPlaylist = data;
                    },
                    'json'
                );
            } 
        });
        $('li.song_play').live('click', function(e) {
            /* use when li.click != a.clikc */
            if( e.target != this ) {
                return true;
            }
            e.preventDefault();
            track = player.parseRenderedTrack($(this));
            var li = $(this);
            
            if (li.parents('div.playlist_track_list').find('#playlist_pk').length) {
                player.playPlaylist(ui.currentUrl, $(this).prevAll().length);
            } else {
                var playlist = player.parseTrackList($(this).parent());
                player.playPlaylist(playlist, $(this).prevAll().length);
            }

            player.hiliteCurrentTrack();
        });
        $('li.song_play .play').live('click', function(e) {
            e.preventDefault();
            $(this).parents('li.song_play').trigger('click');
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
            if (player.ytplayer.isMuted()) {
                player.ytplayer.unMute();
                $(this).css('background-position', 'top left');
            } else {
                player.ytplayer.mute();
                $(this).css('background-position', 'bottom left');
            }
        });
        $('.player_bttn_forw').click(function(e) {
            e.preventDefault();
            player.playNext()
        });
        $('.player_bttn_prev').click(function(e) {
            e.preventDefault();
            player.playPrevious();
        });
        $('.player_bttn_sound').click(function(e) {
            e.preventDefault();
            var level = $(this).attr('class').match(/level_([0-9]+)/)[1];
            player.ytplayer.setVolume(level);
        });
        $('.player_bttn_sound').hover(
            function(e) { /* mouseover */
                var level = $(this).attr('class').match(/level_([0-9]+)/)[1];
                for (var i=0; i < 101; i+=20) {
                    if (i<=level) {
                        $('.player_bttn_sound.level_'+i).css(
                            'background-position',
                            'top left'
                        );
                    } else {
                        $('.player_bttn_sound.level_'+i).css(
                            'background-position',
                            'bottom left'
                        );
                    }
                }
            },
            function(e) { /* mouseout */
                var level = player.ytplayer.getVolume();
                for (var i=0; i < 101; i+=20) {
                    if (i<=level) {
                        $('.player_bttn_sound.level_'+i).css(
                            'background-position',
                            'top left'
                        );
                    } else {
                        $('.player_bttn_sound.level_'+i).css(
                            'background-position',
                            'bottom left'
                        );
                    }
                }
            }
        );
        $('.player_bttn_repeat').hover(
            function(e) {
                if (player.state.repeatMode) {
                    $(this).css('background-position', 'top left');
                } else {
                    $(this).css('background-position', 'bottom left');
                }
            },
            function(e) {
                if (player.state.repeatMode) {
                    $(this).css('background-position', 'bottom left');
                } else {
                    $(this).css('background-position', 'top left');
                }
            }
        );
        $('.player_bttn_repeat').click(function(e) {
            e.preventDefault();

            if (player.state.repeatMode) {
                $(this).css('background-position', 'bottom left');
            } else {
                $(this).css('background-position', 'top left');
            }
            
            player.state.repeatMode = !player.state.repeatMode;
        });
        $('.player_bttn_rand').hover(
            function(e) {
                if (player.state.randomMode) {
                    $(this).css('background-position', 'top left');
                } else {
                    $(this).css('background-position', 'bottom left');
                }
            },
            function(e) {
                if (player.state.randomMode) {
                    $(this).css('background-position', 'bottom left');
                } else {
                    $(this).css('background-position', 'top left');
                }
            }
        );
        $('.player_bttn_rand').click(function(e) {
            e.preventDefault();

            if (player.state.randomMode) {
                $(this).css('background-position', 'bottom left');
            } else {
                $(this).css('background-position', 'top left');
            }
            
            player.state.randomMode = !player.state.randomMode;
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
            $(document).trigger('signalPlaylistTrackModificationRequest', [track, playlist, 'remove', $(this)])
        });
        $('.track_modify').live('click', function(e) {
            if (!user.is_authenticated) {
                return false;
            }
            e.preventDefault();
            var track = player.parseRenderedTrack($(this).parent());
            var playlist = false;
            var action = 'add';
            if(!$(this).hasClass('add_track')){
                action = 'remove';
            }
            /* @todo improve signalPlaylistTrackModificationRequest sig */
            if ($(this).hasClass('tiny_playlist')) {
                playlist = {
                    'pk': tiny_playlist_pk,
                }
                if ($(this).css('backgroundPosition') == 'left bottom') {
                    $(this).css('backgroundPosition', 'left top');
                } else {
                    $(this).css('backgroundPosition', 'left bottom');
                }
            } else if ($('#playlist_pk').length > 0 && $(this).hasClass('noconfirm')) {
                playlist = {
                    'pk': $('#playlist_pk').html(),
                };
            }
            
            $(document).trigger('signalPlaylistTrackModificationRequest', [track, playlist, action, $(this)])

            if ($(this).hasClass('tiny_playlist')) {
                if ($(this).hasClass('remove_track')) {
                    $(this).css('backgroundPosition', 'left top');
                    $(this).removeClass('remove_track');
                    $(this).addClass('add_track');
                    for(i in player.tiny_playlist.tracks) {
                        var compare = player.tiny_playlist.tracks[i];
                        if (compare.name == track.name && compare.artist.name == track.artist.name) {
                            player.tiny_playlist.tracks.splice(i, 1);
                        }
                    }
                    if ($('#playlist_pk').length && $('#playlist_pk').html() == player.tiny_playlist.object.pk) {
                        $(this).parent().fadeOut();
                    }
                } else {
                    $(this).css('backgroundPosition', 'left bottom');
                    $(this).removeClass('add_track');
                    $(this).addClass('remove_track');
                    player.tiny_playlist.tracks.push(track);
                }
            }
        });
        $('#player_bar_control').click(function(e) {
            e = e || window.event;
            
            var divLeft; 
            var obj = document.getElementById('player_bar_control'); 
            
            if(obj.offsetTop){divLeft=obj.offsetLeft;} 
            else if(obj.style.pixelLeft){divLeft=obj.style.pixelLeft;}
            
            //alert(e.clientX - divLeft);
            
            var percent = getPercent(548, e.clientX - divLeft);
            var seconds = player.ytplayer.getDuration() / 100 * percent;
            
            player.ytplayer.seekTo(seconds, true);
        });
    },
    'update': function() {
        if (player.ytplayer.getDuration == undefined) {
            return false;
        }

        var all = player.ytplayer.getDuration();
        var part = player.ytplayer.getCurrentTime();
        var percent = getPercent(all, part);

        var partload = player.ytplayer.getVideoBytesLoaded();
        var allload = player.ytplayer.getVideoBytesTotal();
        var percentload = getPercent(allload, partload);

        var timebarWidth = 548;
        var plState = player.ytplayer.getPlayerState();

        document.getElementById('player_progress_bar').style.width = percent * (timebarWidth / 100) + "px";
        document.getElementById('player_loading_bar').style.width = percentload * (timebarWidth / 100) + "px";

        if(plState==0)
        {
            player.playNext();
        }
    }
}

$(document).ready(function() {
    player.init();
});
