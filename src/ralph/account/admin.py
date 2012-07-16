# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.forms.models import BaseInlineFormSet
from django.utils.translation import ugettext_lazy as _

from lck.django.common.admin import ForeignKeyAutocompleteTabularInline
from tastypie.models import ApiKey

from ralph.account.models import BoundPerm, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    readonly_fields = ('last_active',)
    max_num = 1
    can_delete = False


class ProfileInlineFormSet(BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, **kwargs):
        try:
            instance = instance.get_profile()
        except Exception:
            pass # happens only on object creation
        super(ProfileInlineFormSet, self).__init__(data=data,
            files=files, instance=instance, save_as_new=save_as_new,
            prefix=prefix, queryset=queryset, **kwargs)


class ProfileBoundPermInline(ForeignKeyAutocompleteTabularInline):
    model = BoundPerm
    exclude = ['created', 'modified', 'created_by', 'modified_by', 'role',
            'group']
    related_search_fields = {
        'venture': ['^name'],
    }
    formset = ProfileInlineFormSet

    def __init__(self, parent_model, admin_site):
        self.fk_name = 'profile'
        super(ProfileBoundPermInline, self).__init__(Profile, admin_site)


class ApiKeyInline(admin.StackedInline):
    model = ApiKey
    readonly_fields = ('created',)
    extra = 0


class ProfileAdmin(UserAdmin):
    def groups_show(self):
        return "<br> ".join([g.name for g in self.groups.order_by('name')])
    groups_show.allow_tags = True
    groups_show.short_description = _("groups")

    inlines = [ProfileInline, ProfileBoundPermInline, ApiKeyInline]
    list_display = ('username', 'email', 'first_name', 'last_name',
        groups_show, 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups',)
    save_on_top = True
    search_fields = ('username', 'first_name', 'last_name',
        'email', 'profile__nick')


admin.site.unregister(User)
admin.site.register(User, ProfileAdmin)


class GroupBoundPermInline(ForeignKeyAutocompleteTabularInline):
    model = BoundPerm
    exclude = ['created', 'modified', 'created_by', 'modified_by', 'role',
            'profile']
    related_search_fields = {
        'venture': ['^name'],
    }


class CustomGroupAdmin(GroupAdmin):
    save_on_top = True
    inlines = [GroupBoundPermInline]

admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)
