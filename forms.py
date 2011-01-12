from django import forms
from django.contrib.auth.models import User

class PostRegistrationForm(forms.ModelForm):
    location = forms.CharField(required=True)
    
    def __init__(self, *args, **kwargs):
        if 'initial' not in kwargs.keys():
            kwargs['initial'] = {}

        if kwargs['instance'].playlistprofile.user_location:
            kwargs['initial']['location'] = kwargs['instance'].playlistprofile.user_location

        super(PostRegistrationForm, self).__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.required = True

    def save(self, commit=True):
        self.instance.username = '%s %s' % (
            self.cleaned_data['first_name'],
            self.cleaned_data['last_name']
        )
        self.instance.playlistprofile.user_location = self.cleaned_data['location']
        self.instance.playlistprofile.save()
        return super(PostRegistrationForm, self).save(commit=commit)

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
        )
