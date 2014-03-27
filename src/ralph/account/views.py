#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from bob.menu import MenuItem, MenuHeader
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


from ralph.account.forms import UserHomePageForm
from ralph.account.models import Profile
from ralph.ui.views.common import Base


class BaseUser(Base):
    template_name = 'base.html'

    def get_sidebar_items(self):
        preferences = (
            (
                reverse('user_home_page', args=[]),
                _('Home Page'),
                'fugue-home'
            ), (
                reverse('user_api_key', args=[]),
                _('API Key'),
                'fugue-key'
            ),
        )
        sidebar_items = (
            [MenuHeader('Preferences')] +
            [MenuItem(
                label=preference[1],
                fugue_icon=preference[2],
                href=preference[0]
            ) for preference in preferences]
        )

        return sidebar_items

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseUser, self).get_context_data(**kwargs)
        ret.update({
            'sidebar_items': self.get_sidebar_items(),
        })
        return ret


class ApiKey(BaseUser):
    template_name = 'api_key.html'

    def get_context_data(self, *args, **kwargs):
        ret = super(ApiKey, self).get_context_data(*args, **kwargs)
        ret['api_key'] = self.request.user.api_key.key
        return ret


class BaseUserPreferenceEdit(BaseUser):
    template_name = 'preference.html'
    Form = None
    header = None

    def get(self, *args, **kwargs):
        instance = Profile.objects.get(
            user_id=self.request.user.id,
        )
        self.form = self.Form(instance=instance)
        return super(BaseUserPreferenceEdit, self).get(*args, **kwargs)

    def post(self, *args, **kwargs):
        instance = Profile.objects.get(
            user_id=self.request.user.id,
        )
        self.form = self.Form(self.request.POST, instance=instance)
        if self.form.is_valid():
            self.form.save()
            messages.success(self.request, _("Changes saved."))
        return super(BaseUserPreferenceEdit, self).get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ret = super(BaseUserPreferenceEdit, self).get_context_data(**kwargs)
        ret.update({
            'section': '%s - %s' % (_("User Preference"), self.header),
            'form': self.form,
            'action_url': reverse('user_home_page', args=[]),
            'header': self.header
        })
        return ret


class UserHomePageEdit(BaseUserPreferenceEdit):
    Form = UserHomePageForm
    header = _('Home Page')
