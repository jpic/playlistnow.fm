function Playlist(kwargs) {
    kwargs = kwargs === undefined ? {} : kwargs;

    this.tracks = kwargs.hasOwnProperty('tracks') ? kwargs.tracks : [];
    this.pk = kwargs.hasOwnProperty('pk') ? kwargs.pk : null;
    this.name = kwargs.hasOwnProperty('name') ? kwargs.name : '';
    this.url = kwargs.hasOwnProperty('url') ? kwargs.url : '';
    // backward compatibility
    this.object = this;
}

Playlist.prototype.add = function(track) {
    this.tracks.push(track);
}

Playlist.prototype.remove = function(track) {
    var key, current, i;

    for (i=0; i < this.tracks.length; i++) {
        current = this.tracks[i];

        if (track.pk && track.pk === current.pk) {
            key = i;
            break;
        } else if (track.name && track.artist.name && 
                   track.name === current.name && 
                   track.artist.name === current.artist.name) {
            key = i;
            break;
        } else if (track.name && !track.artist.name && 
                   track.name === current.name) {
            key = i;
            break;
        }
    }

    if (key != undefined) {
        this.tracks.splice(key, 1);
    }
}
