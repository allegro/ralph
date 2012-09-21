#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re
import ipaddr

from django.conf import settings
from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import Named, TimeTrackable
from lck.django.common.models import WithConcurrentGetOrCreate
from dj.choices import Choices
from dj.choices.fields import ChoiceField
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from exceptions import AttributeError

from ralph.discovery.models import DataCenter
from ralph.discovery.models_history import HistoryCost
from ralph.discovery.models_network import Network

from ralph.cmdb.models_ci import CI, CIOwner, CIOwnershipType, CIOwnership

SYNERGY_URL_BASE = settings.SYNERGY_URL_BASE


class PrebootMixin(db.Model):
    preboot = db.ForeignKey('deployment.Preboot', verbose_name=_("preboot"),
            null=True, blank=True, default=None, on_delete=db.SET_NULL)

    class Meta:
        abstract = True

    def get_preboot(self):
        node = self
        while node:
            if node.preboot:
                return node.preboot
            node = node.parent


class Venture(Named, PrebootMixin, TimeTrackable):
    data_center = db.ForeignKey(DataCenter, verbose_name=_("data center"),
        null=True, blank=True)
    parent = db.ForeignKey('self', verbose_name=_("parent venture"), null=True,
        blank=True, default=None, related_name="child_set")
    symbol = db.CharField(verbose_name=_("symbol"), max_length=32,
            blank=True, default="")
    show_in_ralph = db.BooleanField(verbose_name=_("show in ralph"),
            default=False)
    is_infrastructure = db.BooleanField(
            verbose_name=_("this is part of infrastructure"), default=False)
    margin_kind = db.ForeignKey('discovery.MarginKind',
            verbose_name=_("margin kind"), null=True, blank=True, default=None,
            on_delete=db.SET_NULL)
    department = db.ForeignKey('business.Department',
            verbose_name=_("department"), null=True, blank=True, default=None,
            on_delete=db.SET_NULL)
    path = db.TextField(verbose_name=_("symbol path"), blank=True,
            default="", editable=False)
    networks = db.ManyToManyField(Network, null=True, blank=True,
            verbose_name=_("networks list"))

    class Meta:
        verbose_name = _("venture")
        verbose_name_plural = _("ventures")
        unique_together = ('parent', 'symbol')

    def clean(self):
        self.symbol = re.sub(r'[^\w]', '.', self.symbol).lower()

    def save(self, *args, **kwargs):
        if self.parent:
            self.path = self.parent.path + "/" + self.symbol
        else:
            self.path = self.symbol
        super(Venture, self).save(*args, **kwargs)
        for child in self.child_set.all():
            child.save()

    @db.permalink
    def get_absolute_url(self):
        return ("business-show-venture", (), {'venture_id': self.id})

    def technical_owners(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        return CIOwner.objects.filter(ci=ci,
            ciownership__type=CIOwnershipType.technical.id)

    def business_owners(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        return CIOwner.objects.filter(ci=ci,
            ciownership__type=CIOwnershipType.business.id)

    def all_ownerships(self):
        ci = CI.get_by_content_object(self)
        if not ci:
            return []
        return CIOwnership.objects.filter(ci=ci)

    def get_data_center(self):
        if self.data_center:
            return self.data_center
        if self.parent:
            return self.parent.get_data_center()

    def get_margin(self):
        venture = self
        while venture:
            if venture.margin_kind:
                return venture.margin_kind.margin
            venture = venture.parent
        return 0

    def get_department(self):
        if self.department:
            return self.department
        if self.parent:
            return self.parent.get_department()

    def check_ip(self, ip):
        node = self
        while node:
            try:
                for network in node.networks.all():
                    if ipaddr.IPAddress(ip) in ipaddr.IPNetwork(network.address):
                        return True
                node = node.parent
            except AttributeError:
                node = node.parent
        return False

    @property
    def device(self):
        return self.device_set

    @property
    def venturerole(self):
        return self.venturerole_set


class Service(db.Model):
    name = db.CharField(max_length=255, db_index=True)
    external_key = db.CharField(max_length=100,
            unique=True,
            db_index=True
    )
    location = db.CharField(max_length=255)
    state = db.CharField(max_length=100)
    it_person = db.CharField(max_length=255,
            blank=True, default='')
    it_person_mail = db.CharField(max_length=255,
            blank=True, default='')
    business_person = db.CharField(max_length=255,
            blank=True, default='')
    business_person_mail = db.CharField(max_length=255,
            blank=True, default='')
    business_line = db.CharField(max_length=255, blank=False)


class BusinessLine(db.Model):
    name = db.CharField(max_length=255, db_index=True, unique=True)


class VentureRole(Named.NonUnique, PrebootMixin, TimeTrackable):
    venture = db.ForeignKey(Venture, verbose_name=_("venture"))
    parent = db.ForeignKey('self', verbose_name=_("parent role"), null=True,
        blank=True, default=None, related_name="child_set")
    networks = db.ManyToManyField(Network, null=True, blank=True,
                                 verbose_name=_("networks list"))

    class Meta:
        unique_together = ('name', 'venture')
        verbose_name = _("venture role")
        verbose_name_plural = _("venture roles")

    @property
    def full_name(self):
        parents = [self.name]
        obj = self
        while obj.parent:
            obj = obj.parent
            parents.append(obj.name)
        return " / ".join(reversed(parents))

    def check_ip(self, ip):
        node = self
        while node:
            try:
                for network in node.networks.all():
                    if ipaddr.IPAddress(ip) in ipaddr.IPNetwork(network.address):
                        return True
                node = node.parent
            except AttributeError:
                node = node.parent
        return self.venture.check_ip(ip)

    def __unicode__(self):
        return "{} / {}".format(self.venture.symbol if self.venture else '?',
                self.full_name)


class RolePropertyType(db.Model):
    symbol = db.CharField(verbose_name=_("symbol"), max_length=32,
            null=True, default=None, unique=True)

    def __unicode__(self):
        return self.symbol

    class Meta:
        verbose_name = _("property type")
        verbose_name_plural = _("property types")


class RolePropertyTypeValue(db.Model):
    type = db.ForeignKey(RolePropertyType, verbose_name=_("type"), null=True,
        blank=True, default=None)
    value = db.TextField(verbose_name=_("value"), null=True, default=None)

    class Meta:
        verbose_name = _("property type value")
        verbose_name_plural = _("property type values")


class RoleProperty(db.Model):
    symbol = db.CharField(verbose_name=_("symbol"), max_length=32,
            null=True, default=None)
    role = db.ForeignKey(VentureRole, verbose_name=_("role"), null=True,
        blank=True, default=None)
    type = db.ForeignKey(RolePropertyType, verbose_name=_("type"), null=True,
        blank=True, default=None)

    def __unicode__(self):
        return self.symbol

    class Meta:
        unique_together = ('symbol', 'role')
        verbose_name = _("property")
        verbose_name_plural = _("properties")


class RolePropertyValue(db.Model, WithConcurrentGetOrCreate):
    property = db.ForeignKey(RoleProperty, verbose_name=_("property"), null=True,
        blank=True, default=None)
    device = db.ForeignKey('discovery.Device', verbose_name=_("property"), null=True,
        blank=True, default=None)
    value = db.TextField(verbose_name=_("value"), null=True, default=None)

    class Meta:
        unique_together = ('property', 'device')
        verbose_name = _("property value")
        verbose_name_plural = _("property values")

class DepartmentIcon(Choices):
    _ = Choices.Choice

    acorn = _("acorn")
    animal = _("animal")
    animal_dog = _("animal-dog")
    animal_monkey = _("animal-monkey")
    auction_hammer = _("auction-hammer")
    bank = _("bank")
    bomb = _("bomb")
    cactus = _("cactus")
    cake = _("cake")
    cheese = _("cheese")
    flower = _("flower")
    fruit = _("fruit")
    fruit_grape = _("fruit-grape")
    fruit_lime = _("fruit-lime")
    fruit_orange = _("fruit-orange")
    glass = _("glass")
    hamburger = _("hamburger")
    ice_cream = _("ice-cream")
    lollipop = _("lollipop")
    milk = _("milk")
    pearl_shell = _("pearl-shell")
    ribbon = _("ribbon")
    rubber_baloons = _("rubber-baloons")
    shoe = _("shoe")
    snowman = _("snowman")
    sport = _("sport")
    sport_backetball = _("sport-basketball")
    sport_cricket = _("sport-cricket")
    sport_football = _("sport-football")
    sport_golf = _("sport-golf")
    sport_tennis = _("sport-tennis")
    sport_soccer = _("sport-soccer")
    tie = _("tie")
    umbrella = _("umbrella")
    yin_yang = _("yin-yang")


class Department(Named):
    icon = ChoiceField(verbose_name=_("icon"),
        choices=DepartmentIcon, default=None, null=True, blank=True)

    class Meta:
        verbose_name = _("department")
        verbose_name_plural = _("departments")
        ordering = ('name',)


class VentureExtraCostType(Named.NonUnique, TimeTrackable):
    class Meta:
        verbose_name = _("venture extra cost type")
        verbose_name_plural = _("venture extra cost types")
        ordering = ('name',)


class VentureExtraCost(TimeTrackable):
    class Meta:
        verbose_name = _("venture extra cost")
        verbose_name_plural = _("venture extra costs")
        unique_together = ('type', 'venture')
        ordering = ('type',)

    venture = db.ForeignKey(Venture, verbose_name=_("venture"))
    type = db.ForeignKey(VentureExtraCostType, verbose_name=_("type"))
    cost = db.FloatField(verbose_name=_("monthly cost"), default=0)
    expire = db.DateField(default=None, null=True, blank=True)

    @property
    def name(self):
        return self.type.name


@receiver(post_save, sender=VentureExtraCost, dispatch_uid='ralph.costhistory')
def cost_post_save(sender, instance, raw, using, **kwargs):
    changed = False
    if 'venture_id' in instance.dirty_fields:
        changed = True
    if 'expire' in instance.dirty_fields:
        changed = True
    if 'cost' in instance.dirty_fields:
        old_cost = instance.dirty_fields['cost'] or 0
        if not -1 < instance.cost - old_cost < 1:
            # Ignore changes due to rounding errors
            changed = True
    if changed:
        HistoryCost.start_span(extra=instance, end=instance.expire)


@receiver(pre_delete, sender=VentureExtraCost, dispatch_uid='ralph.costhistory')
def cost_pre_delete(sender, instance, using, **kwargs):
    HistoryCost.end_span(extra=instance)
