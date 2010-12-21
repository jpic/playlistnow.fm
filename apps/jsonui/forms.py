# -*- coding: utf-8 -*-

from django import forms
from models import *

class CityForm(forms.Form):
    state = forms.ModelChoiceField(queryset=State.objects.all())
    city = forms.ModelChoiceField(queryset=City.objects.get_empty_query_set())




