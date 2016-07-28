from django.db import models

from ralph.assets.models.base import BaseObject


class DCHostManager(models.Manager):
    select_related_fields = [
        'configuration_path',
        'service_env',
        'service_env__environment',
        'service_env__service',
    ]

    def get_queryset(self):
        return BaseObject.polymorphic_objects.dc_hosts().select_related(
            *self.select_related_fields
        )


class DCHost(BaseObject):
    objects = DCHostManager()

    class Meta:
        proxy = True
