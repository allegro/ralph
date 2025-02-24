#! /usr/bin/python3
import os

import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.getenv('RALPH_DEFAULT_SUPERUSER_NAME', 'ralph')
password = os.getenv('RALPH_DEFAULT_SUPERUSER_PASSWORD', 'ralph')
email = os.getenv('RALPH_DEFAULT_SUPERUSER_EMAIL', '')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
