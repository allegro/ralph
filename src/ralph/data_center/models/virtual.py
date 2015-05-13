# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject


class Database(BaseObject):
    class Meta:
        verbose_name = _('database')
        verbose_name_plural = _('databases')


class VIP(BaseObject):
    class Meta:
        verbose_name = _('VIP')
        verbose_name_plural = _('VIPs')


class VirtualServer(BaseObject):
    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')


class CloudProject(BaseObject):
    pass
