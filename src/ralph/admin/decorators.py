# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from functools import partial
from django.contrib.admin.decorators import register as django_register

from .sites import ralph_site

register = partial(django_register, site=ralph_site)
