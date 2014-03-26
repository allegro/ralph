#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.forms import ChoiceField, ModelForm
from django.utils.translation import ugettext_lazy as _

from ralph.account.models import AvailableHomePage, Profile


class UserHomePageForm(ModelForm):

    class Meta:
        model = Profile
        fields = (
            'home_page',
        )
    home_page = ChoiceField(
        label='Page',
        help_text=_(
            'You will be redirected to this page after login into Ralph.'
        ),
        choices=AvailableHomePage()
    )
