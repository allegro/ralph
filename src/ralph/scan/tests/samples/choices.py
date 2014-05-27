# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from lck.django.choices import Choices


class SampleChoices(Choices):
    _ = Choices.Choice

    simple = _("simple")
    not_simple = _("not simple")
    difficult = _("some difficult case")
