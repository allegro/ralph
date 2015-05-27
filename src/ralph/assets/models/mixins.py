# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


@python_2_unicode_compatible
class NamedMixin(models.Model):
    """Describes an abstract model with a unique ``name`` field."""
    name = models.CharField(_('name'), max_length=50, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    @python_2_unicode_compatible
    class NonUnique(models.Model):
        """Describes an abstract model with a non-unique ``name`` field."""
        name = models.CharField(verbose_name=_("name"), max_length=75)

        class Meta:
            abstract = True

        def __str__(self):
            return self.name


class TimeStampMixin(models.Model):
    created = models.DateTimeField(
        verbose_name=_('date created'),
        auto_now=True,
    )
    modified = models.DateTimeField(
        verbose_name=_('last modified'),
        auto_now_add=True,
    )

    class Meta:
        abstract = True
        ordering = ('-modified', '-created',)

    class Permissions:
        blacklist = set(['created', 'modified'])


class LastSeenMixin(models.Model):
    last_seen = models.DateTimeField(
        verbose_name=_('last seen'),
        auto_now_add=True,
    )

    class Meta:
        abstract = True

    def save(self, update_last_seen=False, *args, **kwargs):
        if update_last_seen:
            self.last_seen = timezone.now()
        super(LastSeenMixin, self).save(*args, **kwargs)
