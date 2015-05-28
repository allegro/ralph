# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ralph.admin.sites import ralph_site
from ralph.admin.mixins import RalphAdmin
from ralph.admin.decorators import register


default_app_config = 'ralph.admin.apps.RalphAdminConfig'

__all__ = [
    'ralph_site', 'default_app_config', 'register', 'RalphAdmin'
]
