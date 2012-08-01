#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from django.conf import settings
from django.db import models as db
from django.utils.translation import ugettext_lazy as _
from lck.django.common.models import Named, TimeTrackable
from lck.django.common.models import WithConcurrentGetOrCreate
from dj.choices import Choices
from dj.choices.fields import ChoiceField
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from ralph.discovery.models import DataCenter
from ralph.discovery.models_history import HistoryCost


SYNERGY_URL_BASE = settings.SYNERGY_URL_BASE


class Venture(Named, TimeTrackable):
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
        return VentureOwner.objects.filter(venture=self,
            type=OwnerType.technical.id)

    def business_owners(self):
        return VentureOwner.objects.filter(venture=self,
            type=OwnerType.business.id)

    def get_data_center(self):
        if self.data_center:
            return self.data_center
        if self.parent:
            return self.parent.get_data_center()

    def get_department(self):
        if self.department:
            return self.department
        if self.parent:
            return self.parent.get_department()

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

class VentureRole(Named.NonUnique, TimeTrackable):
    venture = db.ForeignKey(Venture, verbose_name=_("venture"))
    parent = db.ForeignKey('self', verbose_name=_("parent role"), null=True,
        blank=True, default=None, related_name="child_set")

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


class OwnerType(Choices):
    _ = Choices.Choice

    technical = _("technical owner")
    business = _("business owner")


class VentureOwner(Named.NonUnique, TimeTrackable):
    venture = db.ForeignKey(Venture, verbose_name=_("venture"))
    type = db.PositiveIntegerField(verbose_name=_("type"),
        choices=OwnerType(), default=OwnerType.technical.id)
    synergy_id = db.PositiveIntegerField(verbose_name=_("Synergy ID"),
        null=True, blank=True, default=None)

    class Meta:
        verbose_name = _("venture owner")
        verbose_name_plural = _("venture owners")

    def save(self, *args, **kwargs):
        if self.synergy_id:
            owners = VentureOwner.objects.exclude(
                id=self.id).filter(name=self.name, synergy_id=None).update(
                synergy_id=self.synergy_id)
        if not self.synergy_id:
            owners = VentureOwner.objects.filter(
                name=self.name).exclude(synergy_id=None)
            if owners.count():
                self.synergy_id = owners[0].synergy_id
        super(VentureOwner, self).save(*args, **kwargs)

    def link_if_possible(self):
        if not self.synergy_id:
            return self.name
        else:
            # XXX HTML-escape the name!
            return '<a href="{}docs/HRMResourceCard.aspx?ID={}">{}</a>'.format(
                SYNERGY_URL_BASE, self.synergy_id, self.name)

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


class VentureExtraCost(Named.NonUnique, TimeTrackable):
    class Meta:
        verbose_name = _("venture extra cost")
        verbose_name_plural = _("venture extra costs")
        unique_together = ('name', 'venture')
        ordering = ('name',)

    venture = db.ForeignKey(Venture, verbose_name=_("venture"))
    cost = db.FloatField(verbose_name=_("monthly cost"), default=0)
    expire = db.DateField(default=None, null=True, blank=True)

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

