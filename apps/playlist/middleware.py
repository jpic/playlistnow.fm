class TinyPlaylistMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated:
            request.user.cached_tiny_playlist = Playlist.objects.get(favorite_of=request.user)
