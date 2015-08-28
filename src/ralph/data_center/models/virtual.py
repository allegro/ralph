# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models.base import BaseObject


class Database(BaseObject):
    class Meta:
        verbose_name = _('database')
        verbose_name_plural = _('databases')

    def __str__(self):
        return 'Database: {}'.format(self.service_env)


class VIP(BaseObject):
    class Meta:
        verbose_name = _('VIP')
        verbose_name_plural = _('VIPs')

    def __str__(self):
        return 'VIP: {}'.format(self.service_env)


class VirtualServer(BaseObject):
    class Meta:
        verbose_name = _('Virtual server (VM)')
        verbose_name_plural = _('Virtual servers (VM)')

    def __str__(self):
        return 'VirtualServer: {}'.format(self.service_env)


class CloudProject(BaseObject):

    def __str__(self):
        return 'CloudProject: {}'.format(self.service_env)
