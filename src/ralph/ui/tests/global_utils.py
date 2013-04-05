# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.test.client import Client


def create_user(username='ralph', password='ralph', email='ralph@ralph.local',
                is_staff=True, is_superuser=True):
    """Create user and log him in"""
    user = User.objects.create_user(username, email, password)
    user.is_staff = is_staff
    user.is_superuser = is_superuser
    user.save()
    return user


def login_as_su(username='ralph', password='ralph', email='ralph@ralph.local',
                login=True, is_staff=True, is_superuser=True):
    create_user(username, password, email, is_staff, is_superuser)
    client = Client()
    if login:
        client.login(username=username, password=password)
    return client
