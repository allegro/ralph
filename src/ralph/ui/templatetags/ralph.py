# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from django import template
from django.contrib.staticfiles.storage import staticfiles_storage


register = template.Library()


@register.simple_tag
def extless_static(path):
    """
    A template tag that returns the URL to a file
    using staticfiles' storage backend WITHOUT FILE EXTENSION
    (e.g.: requirejs forcely adds ext. so this is one case why you would wanted)
    """
    path = staticfiles_storage.url(path)
    return os.path.splitext(path)[0]
