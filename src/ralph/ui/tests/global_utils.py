# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test.client import Client


def login_as_su(login='ralph', password='ralph',
    email='ralph@ralph.local', is_staff=True, is_superuser=True):
    user = User.objects.create_user(login, email, password)
    if is_staff:
        user.is_staff = True
    if is_superuser:
        user.is_superuser = True
    user.save()
    client = Client()
    client.login(username=login, password=password)
    return client
