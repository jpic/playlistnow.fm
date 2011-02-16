from django import forms

from models import *

class RecommendationForm(forms.ModelForm):
    class Meta:
        model = Recommendation
        exclude = (
            'creation_date',
            'thank_date',
            'thanks',
            'source',
            'track',
        )
