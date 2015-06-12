# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models


class Foo(models.Model):
    bar = models.CharField('bar', max_length=50)
