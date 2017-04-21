from django.db import models

from ralph.assets.models.base import BaseObject
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin


class DCHostManager(models.Manager):
    def get_queryset(self):
        return BaseObject.polymorphic_objects.dc_hosts()


class DCHost(AdminAbsoluteUrlMixin, BaseObject):
    _allow_in_dashboard = True
    objects = DCHostManager()
    _allow_in_dashboard = True

    class Meta:
        proxy = True
