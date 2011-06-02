function Player(favorites) {
    this.favorites = favorites;
}
Player.prototype.play = function(track) {
  this.currentlyPlayingTrack = track;
  this.isPlaying = true;
};

Player.prototype.pause = function() {
  this.isPlaying = false;
};

Player.prototype.resume = function() {
  if (this.isPlaying) {
    throw new Error("track is already playing");
  }

  this.isPlaying = true;
};

Player.prototype.makeFavorite = function() {
  this.currentlyPlayingTrack.persistFavoriteStatus(true);
};
