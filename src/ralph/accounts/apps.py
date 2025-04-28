# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _

from ralph.apps import RalphAppConfig


class AccountsConfig(RalphAppConfig):
    name = "ralph.accounts"
    verbose_name = _("Accounts")
    default = True

    def ready(self):
        super().ready()
        try:
            import ralph.accounts.ldap  # noqa
        except ImportError:
            pass
