# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import reversion

from django.contrib import admin

from ralph.supports.models import *  # noqa
from ralph.lib.permissions import PermByFieldFormMixin

from django.forms import ModelForm


class SupportForm(PermByFieldFormMixin, ModelForm):
    class Meta:
        model = Support
        fields = [
            'contract_id', 'date_from', 'date_to', 'producer', 'support_type'
        ]


@admin.register(Support)
class SupportAdmin(reversion.VersionAdmin):
    form = SupportForm


@admin.register(SupportType)
class SupportTypeAdmin(reversion.VersionAdmin):
    pass
