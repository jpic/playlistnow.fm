from django import forms
from django.utils.translation import ugettext as _

from models import *

class PlaylistAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PlaylistAddForm, self).__init__(*args, **kwargs)
        self.playlist_categories = PlaylistCategory.objects.filter(parent__isnull=True).select_related(depth=1)

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        if not len(name):
            raise forms.ValidationError('Please fill the name')
        if name == 'chilling, working, eating ...':
            raise forms.ValidationError('Please fill in your own name, this is default name')
        q = Playlist.objects.filter(creation_user=self.user, name__iexact=name)
        if self.instance.pk:
            q = q.exclude(pk=self.instance.pk)
            
        if q.count() > 0:
            raise forms.ValidationError('You already have a playlist with title "%s". Please select another title for this playlist' % name)
        
        return name

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if not len(tags):
            raise forms.ValidationError('Please fill the tags')
        if tags == 'work, eat, chill...':
            raise forms.ValidationError('Please fill in your own tags, these are default tags')
        return tags

    class Meta:
        fields = (
            'name',
            'tags',
            'category',
        )
        model = Playlist
