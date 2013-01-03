# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test.client import Client


def login_as_su(login='ralph', password='ralph', email='ralph@ralph.local'):
    user = User.objects.create_user(login, email, password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    client = Client()
    client.login(username=login, password=password)
    return client
