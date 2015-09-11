# -*- coding: utf-8 -*-
from ralph.admin.mixins import RalphTemplateView


class UserProfileView(RalphTemplateView):

    template_name = 'ralphuser/user_profile.html'
