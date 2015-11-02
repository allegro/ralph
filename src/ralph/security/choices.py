# -*- coding: utf-8 -*-

from dj.choices import Choices


class ScanStatus(Choices):
    _ = Choices.Choice

    ok = _("ok")
    fail = _("fail")
    error = _("error")


class Risk(Choices):
    _ = Choices.Choice

    low = _("low")
    medium = _("medium")
    high = _("high")
