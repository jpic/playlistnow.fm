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
