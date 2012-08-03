#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib.auth.models import User, Group
from django.db import models as db
from django.db.utils import DatabaseError
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from dj.choices import Choices
from dj.choices.fields import ChoiceField
from lck.django.activitylog.models import MonitoredActivity
from lck.django.common.models import TimeTrackable, EditorTrackable
from lck.django.profile.models import BasicInfo, ActivationSupport,\
        GravatarSupport

from ralph.business.models import Venture, VentureRole


class Perm(Choices):
    _ = Choices.Choice

    GLOBAL = Choices.Group(0) << {'per_venture': False}
    read_dc_structure = _("read data center structure")
    edit_ventures_roles = _("edit ventures and roles")
    create_devices = _("create devices")
    delete_devices = _("delete devices")
    edit_device_info_generic = _("edit generic device info")
    edit_device_info_financial = _("edit financial device info")
    edit_device_info_support = _("edit device purchase info")
    run_discovery = _("run discovery")
    read_device_info_management = _("read device management_info")
    read_network_structure = _("read network structure")
    create_configuration_item = _("create configuration items")
    edit_configuration_item_info_generic = _("edit configuration items")
    edit_configuration_item_relations = _("edit configuration item relations")
    read_configuration_item_info_generic = _("read configuration item info generic")
    read_configuration_item_info_puppet = _("read configuration item info Puppet reports")
    read_configuration_item_info_git = _("read configuration item info GIT ")
    read_configuration_item_info_jira = _("read configuration item info jira")
    bulk_edit = _("edit all device info in bulk")
    edit_domain_name = _("edit domain name entries")
    read_domain_name = _("read domain name entries")
    create_device = _("create new devices manually")

    PER_VENTURE = Choices.Group(100) << {'per_venture': True}
    list_devices_generic = _("list venture devices")
    list_devices_financial = _("list venture devices financial info")
    read_device_info_generic = _("read generic device info")
    read_device_info_financial = _("read financial device info")
    read_device_info_support = _("read device purchase info")
    read_device_info_history = _("read device history info")
    read_device_info_reports = _("read device reports")


class Profile(BasicInfo, ActivationSupport, GravatarSupport,
        MonitoredActivity):

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")

    def __unicode__(self):
        return self.nick

    def has_perm(self, perm, obj=None, role=None):
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if isinstance(perm, Choices.Choice):
            groups = self.groups.all()
            if obj:
                return BoundPerm.objects.filter(
                        db.Q(venture=None) |
                            db.Q(venture=obj) |
                            db.Q(venture__parent=obj) |
                            db.Q(venture__parent__parent=obj) |
                            db.Q(venture__parent__parent__parent=obj),
                        db.Q(role=None) |
                            db.Q(role=role) |
                            db.Q(role__parent=role) |
                            db.Q(role__parent__parent=role) |
                            db.Q(role__parent__parent__parent=role),
                        db.Q(profile=self) | db.Q(group__in=groups),
                        perm=perm.id,
                    ).exists()
            else:
                return BoundPerm.objects.filter(
                        db.Q(role=None) | db.Q(role=role),
                        db.Q(profile=self) | db.Q(group__in=groups),
                        venture=None,
                        perm=perm.id,
                    ).exists()
        return super(Profile, self).has_perm(perm, obj)

    def perm_ventures(self, perm):
        """Lists all ventures to which the user has permission."""

        if not self.is_active:
            return []
        groups = self.groups.all()
        if self.is_superuser or BoundPerm.objects.filter(
                db.Q(profile=self) | db.Q(group__in=groups),
                perm=perm.id,
                venture=None,
            ).exists():
            return Venture.objects.all()
        return Venture.objects.filter(
                db.Q(boundperm__profile=self) | db.Q(boundperm__group__in=groups),
                boundperm__perm=perm.id,
            )

    def filter_by_perm(self, query, perm):
        """Filters a device search query according to the permissions."""

        profile = self
        if not profile.is_active:
            return query.none()
        if profile.is_superuser or profile.has_perm(perm):
            return query
        groups = self.groups.all()
        return query.filter(
                db.Q(venture__boundperm__profile=profile,
                  venture__boundperm__perm=perm.id) |
                db.Q(venture__parent__boundperm__profile=profile,
                  venture__parent__boundperm__perm=perm.id) |
                db.Q(venture__parent__parent__boundperm__profile=profile,
                  venture__parent__parent__boundperm__perm=perm.id) |
                db.Q(venture__parent__parent__parent__boundperm__profile=profile,
                  venture__parent__parent__parent__boundperm__perm=perm.id) |
                db.Q(venture__boundperm__group__in=groups,
                  venture__boundperm__perm=perm.id) |
                db.Q(venture__parent__boundperm__group__in=groups,
                  venture__parent__boundperm__perm=perm.id) |
                db.Q(venture__parent__parent__boundperm__group__in=groups,
                  venture__parent__parent__boundperm__perm=perm.id) |
                db.Q(venture__parent__parent__parent__boundperm__group__in=groups,
                  venture__parent__parent__parent__boundperm__perm=perm.id)
            ).distinct()


def create_a_user_profile_ignoring_dberrors(instance):
        try:
            profile, new = Profile.objects.get_or_create(user=instance)
            profile.save() # to trigger nick update etc.
        except DatabaseError:
            pass # no such table yet, first syncdb


@receiver(db.signals.post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    if created:
        create_a_user_profile_ignoring_dberrors(instance)


# ensure at start no user comes without a profile
try:
    for u in User.objects.order_by('id'):
        create_a_user_profile_ignoring_dberrors(u)
except DatabaseError:
    pass # no such table yet, first syncdb
except Exception as e:
    import traceback
    traceback.print_exc()
    raise SystemExit


class BoundPerm(TimeTrackable, EditorTrackable):
    profile = db.ForeignKey(Profile, verbose_name=_("profile"),
            null=True, blank=True, default=None)
    group = db.ForeignKey(Group, verbose_name=_("group"),
            null=True, blank=True, default=None)
    perm = ChoiceField(verbose_name=_("permission"), choices=Perm)
    venture = db.ForeignKey(Venture, verbose_name=_("venture"),
            null=True, blank=True, default=None)
    role = db.ForeignKey(VentureRole, verbose_name=_("venture role"),
            null=True, blank=True, default=None,
            help_text=_("if left empty, the permission applies to all roles "
              "within the selected venture"))

    class Meta:
        verbose_name = _("bound permission")
        verbose_name_plural = _("bound permissions")
