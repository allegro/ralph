# -*- coding: utf-8 -*-
import sys
from imp import reload

from django.conf import settings
from django.core.urlresolvers import clear_url_caches
from django.utils.importlib import import_module

from ralph.tests.factories import UserFactory


class ClientMixin(object):

    def login_as_user(self, user=None, password='ralph', *args, **kwargs):
        if not user:
            user = UserFactory(*args, **kwargs)
            user.is_superuser = True
            user.is_staff = True
            user.save()
        self.user = user
        return self.client.login(username=user.username, password=password)


class ReloadUrlsMixin(object):
    """
    Use this mixin if you register dynamically models to admin.
    """
    def reload_urls(self):
        if settings.ROOT_URLCONF in sys.modules:
            reload(sys.modules[settings.ROOT_URLCONF])
            clear_url_caches()
        return import_module(settings.ROOT_URLCONF)
