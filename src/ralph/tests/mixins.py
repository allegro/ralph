# -*- coding: utf-8 -*-
import sys
from importlib import import_module, reload

from django.conf import settings
from django.urls import clear_url_caches

from ralph.tests.factories import UserFactory


class ClientMixin(object):
    def login_as_user(self, user=None, password="ralph", *args, **kwargs):
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
        """
        Reload all url configs specified in `URLCONF_MODULES` list in settings.

        If there are specific urls for testing, then it's not enough to reload
        only this module, because it's basically (usually) just import main
        urls (including admin urls), which will not be reloaded in only
        ROOT_URLCONF module will be reloaded, thus on that list should be every
        module (spcific, not general module which is proxy to another one, such
        as __init__) which should be reloaded to get fully functional up-to-date
        urls.
        """
        clear_url_caches()
        for urlconf in settings.URLCONF_MODULES:
            if urlconf in sys.modules:
                reload(sys.modules[urlconf])
                import_module(urlconf)
