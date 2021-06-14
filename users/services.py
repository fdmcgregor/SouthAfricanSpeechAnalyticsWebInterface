import datetime
from speech_analytics_platform.celery import app
from django.contrib.auth.models import User
from smtplib import SMTPException
import os

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from six import text_type
from decoding_app.tasks import send_email


class AppTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return (text_type(user.is_active) + text_type(user.pk) + text_type(timestamp))


account_activation_token = AppTokenGenerator()

@app.task(bind=True, default_retry_delay=60, max_retries=120, acks_late=True)
def send_welcome_email_task(self, user_pk, current_site):
    dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Info {dt}: sending welcome email")
    user = User.objects.get(id=user_pk)
    
    # generate link
    uid_instance = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    link = reverse('activate', kwargs={'uidb64': uid_instance, 'token': token})
    activate_url = 'http://'+current_site+link

    email_subject = 'Activate your account'
    email_body = f'Welcome to Saigen {user.username}! Please the follow link to activate your account {activate_url}'
    
    send_email(user.email, email_body, email_subject)

