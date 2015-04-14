# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase
from django.test.client import Client, FakePayload
from factory import (
    Sequence,
    lazy_attribute,
    post_generation,
)
from factory.django import DjangoModelFactory

from ralph.account.models import BoundPerm, Profile, Perm


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

    is_staff = True
    is_superuser = True

    def setUp(self):
        self.user = UserFactory(
            is_staff=self.is_staff,
            is_superuser=self.is_superuser,
        )

        self.headers = {
            'HTTP_ACCEPT': 'application/json',
            'HTTP_AUTHORIZATION': 'ApiKey {}:{}'.format(
                self.user.username, self.user.api_key.key
            ),
        }
        cache.delete("api_user_accesses")
        super(UserTestCase, self).setUp()


    def add_perms(self, perms):
        """Adds a given permission to the test user"""
        user_profile = Profile.objects.get(user=self.user)
        for perm in perms:
            BoundPerm(profile=user_profile, perm=perm).save()

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


def login_as_user(user=None, password='ralph', *args, **kwargs):
    if not user:
        user = UserFactory(*args, **kwargs)
        user.set_password(password)
        user.save()
    client = Client()
    client.login(username=user.username, password=password)
    return client


class GroupFactory(DjangoModelFactory):
    FACTORY_FOR = Group
    name = Sequence(lambda n: 'group_%d' % n)

    @post_generation
    def boundperm_set(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of boundperm_set were passed in, use them
            for group in extracted:
                self.boundperm_set.add(group)


class BoundPermFactory(DjangoModelFactory):
    FACTORY_FOR = BoundPerm
    name = Sequence(lambda n: 'group_%d' % n)


class UserFactory(DjangoModelFactory):
    """
    User *password* is 'ralph'.
    """
    FACTORY_FOR = User

    username = Sequence(lambda n: 'user_{}'.format(n))

    @post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return
        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.groups.add(group)

    @lazy_attribute
    def email(self):
        return '%s@example.com' % self.username

    @classmethod
    def _generate(cls, create, attrs):
        user = super(UserFactory, cls)._generate(create, attrs)
        user.set_password('ralph')
        user.save()
        return user
