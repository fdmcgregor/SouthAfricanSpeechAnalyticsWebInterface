# setup django to access models
import os
import django
import pandas as pd 

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "speech_analytics_platform.settings")
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone

def get_all_logged_in_users():
    # Query all non-expired sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged in users based on id list
    return User.objects.filter(id__in=uid_list)

loggedusers = get_all_logged_in_users()

print(loggedusers)