from django.db import models

from ralph.assets.models.base import BaseObject


class DCHostManager(models.Manager):
    def get_queryset(self):
        return BaseObject.polymorphic_objects.dc_hosts()


class DCHost(BaseObject):
    objects = DCHostManager()

    class Meta:
        proxy = True
