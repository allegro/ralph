# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django.dispatch

post_transition = django.dispatch.Signal(['user', 'assets', 'transition'])

extra_views_kwargs = ('model', 'views')
admin_get_list_views = django.dispatch.Signal(extra_views_kwargs)
admin_get_change_views = django.dispatch.Signal(extra_views_kwargs)
