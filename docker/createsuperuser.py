#!/usr/bin/python
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ralph.settings")
django.setup()

from django.contrib.auth import get_user_model
print('Updating superuser info')
try:
    u = get_user_model().objects.get(username='ralph')
    u.set_password('ralph')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    print('Updated superuser')
except:
    u = get_user_model().objects.create_superuser('ralph', '', 'ralph')
    u.save()
    print('Created superuser')
