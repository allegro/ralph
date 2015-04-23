# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from dj.choices import Country
from django import forms
from django.contrib import admin
from django.forms.models import (
    ModelForm,
    BaseModelFormSet,
    modelformset_factory,
)
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

from lck.django.common.admin import (
    ForeignKeyAutocompleteTabularInline,
    ModelAdmin,
)
from lck.django.profile.admin import ProfileInlineFormSet
from tastypie.models import ApiKey

from ralph.account.models import BoundPerm, Profile, Region


class ProfileInline(admin.StackedInline):
    model = Profile
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


class ApiKeyInline(admin.StackedInline):
    model = ApiKey
    readonly_fields = ('created',)
    extra = 0


class RegionInlineFormSet(BaseModelFormSet):

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance')
        super(RegionInlineFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, *args, **kwargs):
        return super(RegionInlineFormSet, self)._construct_form(
            user_instance=self.instance, *args, **kwargs
        )


class RegionForm(ModelForm):
    assigned = forms.BooleanField(label=_('assigned'), required=False)

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance', None)
        super(RegionForm, self).__init__(*args, **kwargs)
        if self.user_instance:
            objects = Region.profile.through.objects
            self.fields['assigned'].initial = objects.filter(
                region=self.instance,
                profile=self.user_instance.profile
            ).exists()

    def save(self, *args, **kwargs):
        objects = Region.profile.through.objects
        options = {
            'profile': self.user_instance.profile,
            'region': self.cleaned_data['id'],
        }
        if self.cleaned_data['assigned']:
            objects.create(**options)
        else:
            objects.filter(**options).delete()


class RegionInline(admin.TabularInline):
    formset = RegionInlineFormSet
    form = RegionForm
    model = Region
    readonly_fields = ('name',)
    fields = ('name', 'assigned')

    def get_formset(self, *args, **kwargs):
        return modelformset_factory(
            self.model,
            extra=0,
            exclude=['profile', 'name'],
            form=self.form,
            formset=self.formset,
            max_num=1,
        )


class ProfileAdmin(UserAdmin):

    def groups_show(self):
        return "<br> ".join([g.name for g in self.groups.order_by('name')])
    groups_show.allow_tags = True
    groups_show.short_description = _("groups")

    def country(self):
        return Country.raw_from_id(self.profile.country)

    inlines = [
        ProfileInline,
        ProfileBoundPermInline,
        RegionInline,
        ApiKeyInline,
    ]
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        groups_show,
        country,
        'is_staff',
        'is_active',
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


class RegionAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    exclude = ['profile']

admin.site.register(Region, RegionAdmin)
