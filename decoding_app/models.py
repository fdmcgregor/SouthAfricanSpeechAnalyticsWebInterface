import uuid
import json
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import FileExtensionValidator

from .decode_service import decode_audio
    

LANGUAGE_CHOICES = (
    ('eng', 'English'),
    ('afr', 'Afrikaans'),
    ('zul', 'isiZulu'),
    ('sto', 'Sesotho'),
    ('mul', 'Multilingual (En, Af, Zul, Sot)'),
)

SAMPLING_OPTIONS = (
    ('BB', 'Radio (16 kHz)'),
    ('NB', 'Telephone (8 kHz)')
)

FILE_DOWNLOAD_OPTIONS = (
    ('docx', 'Word (.docx)'),
    ('txt', 'Plain text (.txt)'),
    ('json', 'Json word stats (.json)')
)

class Post(models.Model):

    '''
    Post represents the database model where each individual entry has a file and its associated 
    decoded transcript, as well as metadata
    '''

    # metadata
    title = models.CharField(max_length=255, blank=True, verbose_name="Name (default is audio file name)")
    date_posted = models.DateTimeField(default=timezone.now)
    date_complete = models.DateTimeField(default=timezone.now)
    slug = models.SlugField(max_length=100)
    
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=6, choices=LANGUAGE_CHOICES, default='en')
    sampling_freq = models.CharField(max_length=6, choices=SAMPLING_OPTIONS, default='WB', verbose_name="Audio Quality")

    # audio file field
    audio_file = models.FileField(upload_to='media/audio_uploads/', max_length=255)
    
    # generated data
    transcription = models.TextField(default="Busy decoding...")
    audio_length = models.IntegerField(default=0)
    words_json = models.TextField(default='[{"confidence": 1.00, "endTime": 0.01, "startTime": 0.00, "word": "Busy decoding..."}]')

    # preferences
    delete_after_transcription = models.BooleanField(default=False, verbose_name="Delete file(s) after transcription?")
    automatic_punctuation = models.BooleanField(default=False, verbose_name="Automatic punctuation")
    automatic_diarization = models.BooleanField(default=False, verbose_name="Automatic speaker diarization")
    num_speakers = models.IntegerField(default=-1)
    file_type = models.CharField(max_length=6, choices=FILE_DOWNLOAD_OPTIONS, default='docx', verbose_name="Preferred file type")

    done_decoding = models.BooleanField(default=False)
    
    
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        '''
        This method is called once the upload form is validated, will and either redirect the user
        to the home page if the the user wants to delete the data after transcribing or to the 
        page with transcription (detail view).
        '''

        if self.delete_after_transcription:
            return reverse('decoding-app-home')
        else:
            return reverse('post-detail', kwargs={'pk': self.pk})



    def delete(self, *args, **kwargs):
        '''
        Overide the delete method to also delete the stored audio file if the user deletes a
        post.
        '''
        self.audio_file.delete()
        super().delete(*args, **kwargs)
    

class SearchQuery(models.Model):
    keyword = models.CharField(max_length=100)
    post_pk = models.CharField(max_length=100, default='None')
    date_searched = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.keyword


class GlobalQuery(models.Model):

    keyword = models.CharField(max_length=100)
    date_searched = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.keyword

