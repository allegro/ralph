# -*- coding: utf-8 -*-

from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import UserAdmin

from ralph.admin import RalphAdmin, register


@register(Group)
class GroupAdmin(RalphAdmin):
    pass


@register(User)
class RalpgUserAdmin(UserAdmin, RalphAdmin):
    pass
