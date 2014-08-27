#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import functools


from django.conf import settings
from django.contrib.auth.models import Group
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import models as db
from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _


from dj.choices import Choices
from dj.choices.fields import ChoiceField
from lck.django.activitylog.models import MonitoredActivity
from lck.django.common.models import TimeTrackable, EditorTrackable
from lck.django.profile.models import (
    BasicInfo,
    ActivationSupport,
    GravatarSupport,
)

from ralph.business.models import Venture, VentureRole


class AvailableHomePage(Choices):
    _ = Choices.Choice
    default = _('Default home page')
    ventures = _("Ventures list")
    racks = _("Racks list")
    networks = _("Network list")
    reports = _("Reports")
    catalog = _("Catalog")
    cmdb_timeline = _("CMDB timeline")


class Perm(Choices):
    _ = Choices.Choice

    GLOBAL = Choices.Group(0).extra(per_venture=False)
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
    read_configuration_item_info_generic = _(
        "read configuration item info generic")
    read_configuration_item_info_puppet = _(
        "read configuration item info Puppet reports")
    read_configuration_item_info_git = _("read configuration item info GIT ")
    read_configuration_item_info_jira = _("read configuration item info jira")
    bulk_edit = _("edit all device info in bulk")
    edit_domain_name = _("edit domain name entries")
    read_domain_name = _("read domain name entries")
    create_device = _("create new devices manually")
    read_deployment = _("read deployment")

    PER_VENTURE = Choices.Group(100) << {'per_venture': True}
    list_devices_generic = _("list venture devices")
    list_devices_financial = _("list venture devices financial info")
    read_device_info_generic = _("read generic device info")
    read_device_info_financial = _("read financial device info")
    read_device_info_support = _("read device purchase info")
    read_device_info_history = _("read device history info")
    read_device_info_reports = _("read device reports")
    has_assets_access = _("has_assets_access")
    has_core_access = _("has_core_access")
    has_scrooge_access = _("has_scrooge_access")


class Profile(BasicInfo, ActivationSupport, GravatarSupport,
              MonitoredActivity):

    class Meta:
        verbose_name = _("profile")
        verbose_name_plural = _("profiles")

    home_page = ChoiceField(
        choices=AvailableHomePage,
        default=AvailableHomePage.default,
    )

    # TODO: define fields below and add AUTH_LDAP_PROFILE_ATTR_MAP mappings
    company = db.CharField(max_length=64, blank=True)
    employee_id = db.CharField(max_length=64, blank=True)
    profit_center = db.CharField(max_length=1024, blank=True)
    cost_center = db.CharField(max_length=1024, blank=True)
    department = db.CharField(max_length=64, blank=True)
    manager = db.CharField(max_length=1024, blank=True)
    location = db.CharField(max_length=128, blank=True)

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


class BoundPerm(TimeTrackable, EditorTrackable):
    profile = db.ForeignKey(
        Profile,
        verbose_name=_("profile"),
        null=True,
        blank=True,
        default=None,
    )
    group = db.ForeignKey(
        Group,
        verbose_name=_("group"),
        null=True,
        blank=True,
        default=None,
    )
    perm = ChoiceField(verbose_name=_("permission"), choices=Perm)
    venture = db.ForeignKey(
        Venture,
        verbose_name=_("venture"),
        null=True,
        blank=True,
        default=None,
    )
    role = db.ForeignKey(
        VentureRole,
        verbose_name=_("venture role"),
        null=True,
        blank=True,
        default=None,
        help_text=_("if left empty, the permission applies to all roles "
                    "within the selected venture"),
    )

    class Meta:
        verbose_name = _("bound permission")
        verbose_name_plural = _("bound permissions")


def ralph_permission(perms=None):
    """
    Decorator responsible for checking user's permissions to a given view.
    Permissions to check should be specified in the following way:
        perms = [
            {
                'perm': Perm.read_device_info_reports,
                'msg': _("You don't have permission to see reports.")
            }
        ]
    If no permissions are specified, 'Perm.has_core_access' will be used.
    """

    if not perms:
        perms = [
            {
                'perm': Perm.has_core_access,
                'msg': _("You don't have permissions for this resource."),
            },
        ]

    def decorator(func):
        def inner_decorator(self, *args, **kwargs):
            from ralph.account.views import HTTP403
            from ralph.util import api
            # class-based views
            if args and isinstance(args[0], WSGIRequest):
                request = args[0]
            # function-based views
            elif self and isinstance(self, WSGIRequest):
                request = self
            # check for request in kwargs as well, just in case
            elif 'request' in kwargs:
                request = kwargs['request']
            else:
                return HttpResponseBadRequest()
            user = request.user
            # for API views not handled by Tastypie (e.g. puppet_classifier)
            if user.is_anonymous():
                user = api.get_user(request)
                if not api.is_authenticated(user, request):
                    return HTTP403(request)
            profile = user.get_profile()
            has_perm = profile.has_perm
            for perm in perms:
                if not has_perm(perm['perm']):
                    return HTTP403(request, perm['msg'])
            return func(self, *args, **kwargs)
        # helper property for unit tests
        func.decorated_with = 'ralph_permission'
        return functools.wraps(func)(inner_decorator)
    return decorator


def get_user_home_page_url(user):
    profile = user.get_profile()
    if profile.home_page == AvailableHomePage.default:
        try:
            home_page = reverse(settings.HOME_PAGE_URL_NAME, args=[])
        except NoReverseMatch:
            home_page = reverse('search')
    else:
        home_page = reverse(profile.home_page.name)
    return home_page
