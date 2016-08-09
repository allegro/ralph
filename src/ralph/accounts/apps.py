# -*- coding: utf-8 -*-
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from ralph.apps import RalphAppConfig


def update_modified_date(sender, instance, **kwargs):
    # TODO: update users belongs to group
    pass


class AccountsConfig(RalphAppConfig):
    name = 'ralph.accounts'
    verbose_name = _('Accounts')

    # def ready(self):
    #     from django.contrib.auth.models import Group
    #     super().ready()
    #     post_save(update_modified_date, Group)
