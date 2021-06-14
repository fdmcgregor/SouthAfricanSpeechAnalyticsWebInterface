import os
import io
import requests
import json
from time import time
from django.core.serializers.json import DjangoJSONEncoder
from django.apps import apps
from django.conf import settings
import boto3
import urllib.parse
from celery import shared_task
import datetime
from django.utils import timezone

from .services import json_to_diarized_txt
from .tasks import send_transcription_email, send_email

@shared_task(bind=True, max_retries=1)
def decode_audio(self, pk):

    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Info {dt}: decoding pk {pk}")

    try:
        Post = apps.get_model(app_label='decoding_app', model_name='Post')
        post = Post.objects.get(pk=pk)
        
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{dt} decoding {post}")
        
        # job details
        sac = "yes" if post.automatic_punctuation else "no"
        dia = "yes" if post.automatic_diarization else "no"
        sf = post.sampling_freq if post.language == 'eng' or post.language == 'afr' else "NB"
        URL = os.environ.get('LAMBDA_URL')

        request_params = {
                'X_API_KEY': os.environ.get('LAMBDA_API_KEY'),
                'JOB_ID': str(post.slug),
                'USER_ID': str(post.author.pk),
                'DEC_LANG': str(post.language),
                'SR': str(sf),
                'SAC': str(sac),
                'DIA': str(dia),
                'NUM_SPK': str(post.num_speakers),
                'BATCHED': str(0),
                'NUM_CHANNELS': "1",
                "BUCKET_NAME" : os.environ.get('AWS_STORAGE_BUCKET_NAME'),
                "SOURCE" : 'url',
                "RETURN_URL" : 'https://www.saigendsac.com/jobcomplete/',
                "OBJECT_PATH" : post.audio_file.name,
            }

        #request_params['RETURN_URL'] = f'http://{os.environ.get("HOST_IP")}:8000/jobcomplete/'

        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{dt}: Sending request to API with URL")
        print(request_params)

        try:
            r = requests.post(URL, headers=request_params)
        finally:
            print(f"Response: {r.text}")

            if r.status_code == 200:

                # job submitted
                print("SUCESS: job submitted")
                post.job_status = 'submitted'
                post.transcription = "Submitted."
                post.words_json = '[{"confidence": 1.00, "endTime": 0.01, "startTime": 0.00, "word": "Submitted. "}]'
                post.save()

            else:
                print("ERROR: job submission failure")

                post.job_status = 'submitted'

                # update transcription
                post.transcription = "Upload failure."
                post.words_json = '[{"confidence": 1.00, "endTime": 0.01, "startTime": 0.00, "word": "Upload failure. "}]'
                post.audio_length = 0
                post.done_decoding = False

                # send transcrption
                if settings.DEBUG is False:
                    send_email(post.author.email, post.transcription, f'Transcription for {post.title} failed')

                if post.delete_after_transcription == True:
                    post.audio_file.delete()

                post.save()

                return f"{dt}: Failed upload {post.pk}!"

    
    except Post.DoesNotExist:
        return f"{dt}: COULD NOT FIND {pk} for user {post.author}!"

    return f"{dt}: Submitted {post.pk} slug -> {post.slug}!"

def save_api_response(slug, payload):
    
    Post = apps.get_model(app_label='decoding_app', model_name='Post')
    post = Post.objects.filter(slug=slug)[0]
    pk = post.pk
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{dt}: saving pk {pk}")

    # save transcription
    transcript = payload['results'][0]['alternatives'][0]['transcript']
    json_words = payload['results'][0]['alternatives'][0]['words']
    post.transcription = transcript
    post.done_decoding = True
    post.words_json = json.dumps(json_words,cls=DjangoJSONEncoder)
    post.save()

    # update user account
    profile = post.author.profile
    profile.total_seconds = profile.total_seconds + post.audio_length
    profile.save()

    # if delete, send transcription and delete
    if post.delete_after_transcription == True:
        # dont save transcription and delete audio file
        post.audio_file.delete()
        post.transcription = "Not saved"
        post.words_json = "Not saved"

        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{dt} Before removing data: Send email")

        # mangage diarization for transcript
        words_json_to_send = json.dumps(json_words,cls=DjangoJSONEncoder)
        if post.automatic_diarization:
            transcript = json_to_diarized_txt(json.loads(words_json_to_send))
        else:
            transcript = payload['results'][0]['alternatives'][0]['transcript']
        send_transcription_email.delay(post.author.email, transcript, post.file_type, \
                                words_json_to_send, post.title, post.automatic_diarization)
        
    else:
        # save word level transcript details
        post.words_json = json.dumps(json_words,cls=DjangoJSONEncoder)

    post.date_complete = timezone.now()
    post.save()

    # send transcrption
    if post.delete_after_transcription == False:
        
        dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{dt} Sending email")
        
        # mangage diarization for transcript
        if post.automatic_diarization:
            transcript = json_to_diarized_txt(json.loads(post.words_json))
        else:
            transcript = post.transcription

        send_transcription_email(post.author.email, transcript, post.file_type, \
                                post.words_json, post.title, post.automatic_diarization)

    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{dt}: Saved decoding {post.pk}!")

    return f"Saved decoding {post.pk}!"

