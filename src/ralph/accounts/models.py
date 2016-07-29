# -*- coding: utf-8 -*-

from dj.choices import Country, Gender
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token

from ralph.admin.autocomplete import AutocompleteTooltipMixin
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, NamedMixin
from ralph.lib.permissions import (
    PermByFieldMixin,
    PermissionsForObjectMixin,
    user_permission
)


@user_permission
def has_region(user):
    """
    Check if user has rights to region.
    """
    return models.Q(id__in=user.regions_ids)


class Region(PermissionsForObjectMixin, NamedMixin):
    country = models.PositiveIntegerField(
        verbose_name=_('country'),
        choices=Country(),
        default=Country.pl.id,
    )
    stocktaking_enabled = models.BooleanField(default=False)

    """Used for distinguishing the origin of the object by region"""
    class Permissions:
        has_access = has_region


@user_permission
def object_has_region(user):
    """
    Check if object's region is one of user regions.
    """
    return models.Q(region__in=user.regions_ids)


class Regionalizable(PermissionsForObjectMixin):
    region = models.ForeignKey(Region, blank=False, null=False)

    class Meta:
        abstract = True

    class Permissions:
        has_access = object_has_region


class Team(NamedMixin):
    pass


class RalphUser(
    PermByFieldMixin,
    AbstractUser,
    AdminAbsoluteUrlMixin,
    AutocompleteTooltipMixin
):

    gender = models.PositiveIntegerField(
        verbose_name=_('gender'),
        choices=Gender(),
        default=Gender.male.id,
    )
    country = models.PositiveIntegerField(
        verbose_name=_('country'),
        choices=Country(),
        default=Country.pl.id,
    )
    city = models.CharField(
        verbose_name=_("city"),
        max_length=30,
        blank=True,
    )
    company = models.CharField(
        verbose_name=_('company'),
        max_length=64,
        blank=True,
    )
    employee_id = models.CharField(
        verbose_name=_('employee id'),
        max_length=64,
        blank=True,
    )
    profit_center = models.CharField(
        verbose_name=_('profit center'),
        max_length=1024,
        blank=True,
    )
    cost_center = models.CharField(
        verbose_name=_('cost center'),
        max_length=1024,
        blank=True,
    )
    department = models.CharField(
        verbose_name=_('department'),
        max_length=64,
        blank=True,
    )
    manager = models.CharField(
        verbose_name=_('manager'),
        max_length=1024,
        blank=True,
    )
    location = models.CharField(
        verbose_name=_('location'),
        max_length=128,
        blank=True,
    )
    segment = models.CharField(
        verbose_name=_('segment'),
        max_length=256,
        blank=True,
    )
    regions = models.ManyToManyField(Region, related_name='users', blank=True)
    team = models.ForeignKey(Team, null=True, blank=True)

    autocomplete_tooltip_fields = [
        'employee_id',
        'company',
        'department',
        'manager',
        'profit_center',
        'cost_center'
    ]
    autocomplete_words_split = True

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return '{} ({})'.format(full_name, self.username)
        return super().__str__()

    @property
    def api_token_key(self):
        try:
            return self.auth_token.key
        except Token.DoesNotExist:
            return None

    @property
    def regions_ids(self):
        """
        Get region ids without additional SQL joins.
        """
        return self.regions.through.objects.filter(
            ralphuser=self
        ).values_list(
            'region_id', flat=True
        )

    def has_any_perms(self, perms, obj=None):
        return any([self.has_perm(p, obj=obj) for p in perms])

    def save(self, *args, **kwargs):
        # set default values if None provided
        for field in ('gender', 'country'):
            val = getattr(self, field)
            if val is None:
                val = self._meta.get_field_by_name(field)[0].default
                setattr(self, field, val)
        return super().save(*args, **kwargs)

    @property
    def autocomplete_str(self):
        return '{} <i>{}</i>'.format(str(self), self.department)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    Create token for newly created user.
    """
    if created:
        Token.objects.create(user=instance)
