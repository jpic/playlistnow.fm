from django import forms
from django.utils.translation import ugettext as _

from models import *

class PlaylistAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlaylistAddForm, self).__init__(*args, **kwargs)
        self.playlist_categories = PlaylistCategory.objects.filter(parent__isnull=True).select_related(depth=1)

    class Meta:
        fields = (
            'name',
            'tags',
            'category',
        )
        model = Playlist
