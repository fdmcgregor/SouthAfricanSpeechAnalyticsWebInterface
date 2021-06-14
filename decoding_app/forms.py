from django.forms import ModelForm
from django import forms

from .models import SearchQuery, GlobalQuery, Post

class PostForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Post
        fields = [  'language', 'sampling_freq',
                    'file_type',
                    'delete_after_transcription',
                    'automatic_punctuation',
                    'automatic_diarization',
                ]

class SearchKeywordQueryForm(ModelForm):

    class Meta:
        model = SearchQuery
        fields = ['keyword']

        widgets = {'keyword': forms.TextInput(attrs={'class': 'form-control'})}


class GlobalSearchForm(ModelForm):

    class Meta:
        model = GlobalQuery
        fields = ['keyword']
        widgets = {'keyword': forms.TextInput(attrs={'class': 'form-control'})}