# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client, FakePayload


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


class UserTestCase(TestCase):
    """A test case that creates a user and allows to test API with it."""

    def setUp(self):
        self.user = create_user('api_user', 'test@mail.local', 'password')
        self.headers = {
            'HTTP_ACCEPT': 'application/json',
            'HTTP_AUTHORIZATION': 'ApiKey {}:{}'.format(
                self.user.username, self.user.api_key.key
            ),
        }
        cache.delete("api_user_accesses")
        super(UserTestCase, self).setUp()

    def generic_method(method, default_data):
        def result(self, path, data=default_data, **kwargs):
            full_kwargs = self.headers.copy()
            full_kwargs.update(kwargs)
            return getattr(self.client, method)(path, data, **full_kwargs)
        return result

    post = generic_method('post', '')
    put = generic_method('put', '')
    get = generic_method('get', {})

    def patch(self, path, data, **kwargs):
        req_data = self.headers.copy()
        req_data.update({
            'CONTENT_LENGTH': len(data),
            'REQUEST_METHOD': 'PATCH',
            'PATH_INFO': path,
            'wsgi.input': FakePayload(data)
        })
        return self.client.request(**req_data)

