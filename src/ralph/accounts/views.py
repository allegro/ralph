# -*- coding: utf-8 -*-
from django.views.generic import TemplateView

from ralph.accounts.admin import UserInfoMixin
from ralph.admin.mixins import RalphTemplateView


class UserProfileView(RalphTemplateView):
    template_name = 'ralphuser/user_profile.html'


class CurrentUserInfoView(UserInfoMixin, TemplateView):
    template_name = 'ralphuser/my_equipment.html'

    def get_user(self):
        return self.request.user
