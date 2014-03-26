# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

from lck.django.activitylog.admin import IPInline, UserAgentInline
from lck.django.common.admin import ForeignKeyAutocompleteTabularInline
from lck.django.profile.admin import ProfileInlineFormSet
from tastypie.models import ApiKey

from ralph.account.models import BoundPerm, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    readonly_fields = ('last_active',)
    max_num = 1
    can_delete = False


class ProfileBoundPermInline(ForeignKeyAutocompleteTabularInline):
    model = BoundPerm
    exclude = [
        'created',
        'modified',
        'created_by',
        'modified_by',
        'role',
        'group'
    ]
    related_search_fields = {
        'venture': ['^name'],
    }
    formset = ProfileInlineFormSet

    def __init__(self, parent_model, admin_site):
        self.fk_name = 'profile'
        super(ProfileBoundPermInline, self).__init__(Profile, admin_site)


class ProfileIPInline(IPInline):
    formset = ProfileInlineFormSet

    def __init__(self, parent_model, admin_site):
        self.fk_name = 'profile'
        super(ProfileIPInline, self).__init__(Profile, admin_site)


class ProfileUserAgentInline(UserAgentInline):
    formset = ProfileInlineFormSet

    def __init__(self, parent_model, admin_site):
        self.fk_name = 'profile'
        super(ProfileUserAgentInline, self).__init__(Profile, admin_site)


class ApiKeyInline(admin.StackedInline):
    model = ApiKey
    readonly_fields = ('created',)
    extra = 0


class ProfileAdmin(UserAdmin):

    def groups_show(self):
        return "<br> ".join([g.name for g in self.groups.order_by('name')])
    groups_show.allow_tags = True
    groups_show.short_description = _("groups")

    inlines = [
        ProfileInline,
        ProfileBoundPermInline,
        ApiKeyInline,
        ProfileIPInline,
        ProfileUserAgentInline,
    ]
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        groups_show,
        'is_staff',
        'is_active'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',)
    save_on_top = True
    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'profile__nick'
    )

    def get_formsets(self, request, obj=None):
        """Skips inlines in add form.

        See: https://github.com/allegro/ralph/issues/495
        """
        if not obj:
            return
        for formset in super(ProfileAdmin, self).get_formsets(
            request, obj=obj,
        ):
            yield formset


admin.site.unregister(User)
admin.site.register(User, ProfileAdmin)


class GroupBoundPermInline(ForeignKeyAutocompleteTabularInline):
    model = BoundPerm
    exclude = [
        'created',
        'modified',
        'created_by',
        'modified_by',
        'role',
        'profile'
    ]
    related_search_fields = {
        'venture': ['^name'],
    }


class CustomGroupAdmin(GroupAdmin):
    save_on_top = True
    inlines = [GroupBoundPermInline]

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
