describe("Player", function() {
  var player;
  var track;

  beforeEach(function() {
    player = new Player();
    track = new Track();
  });

  it("should be able to play a Track", function() {
    player.play(track);
    expect(player.currentlyPlayingTrack).toEqual(track);

    //demonstrates use of custom matcher
    expect(player).toBePlaying(track);
  });

  describe("when track has been paused", function() {
    beforeEach(function() {
      player.play(track);
      player.pause();
    });

    it("should indicate that the track is currently paused", function() {
      expect(player.isPlaying).toBeFalsy();

      // demonstrates use of 'not' with a custom matcher
      expect(player).not.toBePlaying(track);
    });

    it("should be possible to resume", function() {
      player.resume();
      expect(player.isPlaying).toBeTruthy();
      expect(player.currentlyPlayingTrack).toEqual(track);
    });
  });

  // demonstrates use of spies to intercept and test method calls
  it("tells the current track if the user has made it a favorite", function() {
    spyOn(track, 'persistFavoriteStatus');

    player.play(track);
    player.makeFavorite();

    expect(track.persistFavoriteStatus).toHaveBeenCalledWith(true);
  });

  //demonstrates use of expected exceptions
  describe("#resume", function() {
    it("should throw an exception if track is already playing", function() {
      player.play(track);

      expect(function() {
        player.resume();
      }).toThrow("track is already playing");
    });
  });
});

