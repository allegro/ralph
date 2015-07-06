# -*- coding: utf-8 -*-

from dj.choices import (
    Country,
    Gender,
)
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class RalphUser(AbstractUser):

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

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    def save(self, *args, **kwargs):
        # set default values if None provided
        for field in ('gender', 'country'):
            val = getattr(self, field)
            if val is None:
                val = self._meta.get_field_by_name(field)[0].default
                setattr(self, field, val)
        return super().save(*args, **kwargs)
