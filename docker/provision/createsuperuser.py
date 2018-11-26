#! /usr/bin/python3
import os

import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ['RALPH_ADMIN_USERNAME']
password = os.environ['RALPH_ADMIN_PASSWORD']
email = os.environ['RALPH_ADMIN_EMAIL']

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
