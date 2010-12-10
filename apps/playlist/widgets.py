from django.forms import widget

class PlaylistCategoryWidget(Select):
    def __init__(self, attrs=None, choices=()):
        print choices
