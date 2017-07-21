#!/usr/bin/python
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ralph.settings")
django.setup()

print('Updating superuser info')
u = get_user_model().objects.get(
    username=os.getenv('RALPH_SUPERUSER_NAME', 'ralph')
)
u.set_password(
    os.getenv('RALPH_SUPERUSER_PASSWORD', 'ralph')
)
u.is_superuser = True
u.is_staff = True
u.save()
