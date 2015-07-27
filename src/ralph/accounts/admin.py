# -*- coding: utf-8 -*-
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import RalphUser
from ralph.admin import RalphAdmin, register


@register(RalphUser)
class RalphUserAdmin(UserAdmin, RalphAdmin):

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions'
            )
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
        (_('Profile'), {
            'fields': (
                'gender', 'country', 'city',
            )
        }),
        (_('Job info'), {
            'fields': (
                'company', 'profit_center', 'cost_center', 'department',
                'manager', 'location', 'segment'
            )
        })
    )


@register(Group)
class RalphGroupAdmin(GroupAdmin, RalphAdmin):
    pass
