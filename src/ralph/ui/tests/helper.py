# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test.client import Client


def login_as_su(username='ralph', password='ralph', email='ralph@ralph.local',
                login=True):
    user = User.objects.create_user(username, email, password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    client = Client()
    if login:
        client.login(username=username, password=password)
    return client
