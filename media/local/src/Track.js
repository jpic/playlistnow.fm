function Track(kwargs) {
    kwargs = kwargs === undefined ? {} : kwargs;

    this.name = kwargs.hasOwnProperty('name') ? kwargs.name : '';
    this.url = kwargs.hasOwnProperty('url') ? kwargs.url : '';
    this.artist = kwargs.hasOwnProperty('artist') ? kwargs.artist : new Artist();
    this.youtube_id = kwargs.hasOwnProperty('youtube_id') ? kwargs.youtube_id : '';
}

Track.prototype.persistFavoriteStatus = function(value) {

  throw new Error("not yet implemented");
}

$('li.song_play').live('click', function(e) {
    var context, activity, playlist, link;

    context = $('#page_body_wrapper');
    activity = $(this).parents('div.lineFeedContentWhat');
    // if tiny playlist: actor tiny playlist
    try {
        playlist = activity.find('.feed_likes a.playlist.detail').attr('href');
    } catch (e) {
        playlist = false;
    }
    // if playlist page: current playlist
    try {
        playlist = $('div.gory_detail a.playlist.detail').attr('href');
    } catch(e) {
        playlist = false;
    }

    if (playlist) {
        playlist = Model.fetchPlaylist(playlist);
    }
    // if artist page: playlist is radio
    if (context.find('.artist.radio').length == 1) {
        playlist = Model.fetchPlaylist(context.find(
            '.artist.radio a.play_playlist_json_url').attr('href'));
    }
    // if add to playlist activity: playlist
    else if (activity) {
        link = activity.find('a.playlist')
        Model.fetchPlaylist(link.attr('href'))
    }
});
