from django.db import models
from django.contrib.auth.models import User

User._meta.get_field('email')._unique = True


LANGUAGE_CHOICES = (
    ('eng', 'English'),
    ('afr', 'Afrikaans'),
    ('zul', 'Zulu'),
    ('stu', 'Sotho'),
    ('mul', 'Multilingual (En, Af, Zul, Sot)'),
)

SAMPLING_OPTIONS = (
    ('WB', 'Radio (16 kHz)'),
    ('NB', 'Telephone (8 kHz)')
)

FILE_DOWNLOAD_OPTIONS = (
    ('docx', 'Word (.docx)'),
    ('txt', 'Plain text (.txt)'),
    ('json', 'Json word stats (.json)')
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    total_seconds = models.IntegerField(default=0)
    total_amount = models.FloatField(default=0.0)

    # preferences
    sampling_freq = models.CharField(max_length=6, choices=SAMPLING_OPTIONS, default='WB', 
                                     verbose_name="Set your default audio quality or \
                                     samplng frequency for new files.")
    language = models.CharField(max_length=6, choices=LANGUAGE_CHOICES, default='en',
                                verbose_name="Set your default language for new files.")
  

    delete_after_transcription = models.BooleanField(default=False,
                                                     verbose_name="Delete files after transcription?\
                                                     Set your default preference for new files.")
    
    automatic_punctuation = models.BooleanField(default=False,
                                        verbose_name="Automatic punctuation?\
                                                     Set your default preference for new files.")
    automatic_diarization = models.BooleanField(default=False,
                                        verbose_name="Automatic speaker diarization?\
                                                     Set your default preference for new files.")

    file_type = models.CharField(max_length=6, choices=FILE_DOWNLOAD_OPTIONS, default='docx',
                                    verbose_name="Set your default file type to recieve\
                                    transcriptions for new files.")
    
    
    # backup flag to allow user to always decode
    allow_decoding_overide = models.BooleanField(default=False)


    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

