# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import Group, User
from django.test.client import Client
from factory import (
    Sequence,
    lazy_attribute,
    post_generation,
)
from factory.django import DjangoModelFactory

from ralph.account.models import BoundPerm


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
