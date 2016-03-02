# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from taggit.managers import TaggableManager
from taggit.forms import TagField


class NamedMixin(models.Model):
    """Describes an abstract model with a unique ``name`` field."""
    name = models.CharField(_('name'), max_length=255, unique=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name

    class NonUnique(models.Model):
        """Describes an abstract model with a non-unique ``name`` field."""
        name = models.CharField(verbose_name=_("name"), max_length=75)

        class Meta:
            abstract = True
            ordering = ['name']

        def __str__(self):
            return self.name


class TimeStampMixin(models.Model):
    created = models.DateTimeField(
        verbose_name=_('date created'),
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        verbose_name=_('last modified'),
        auto_now=True,
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


class AdminAbsoluteUrlMixin(object):
    def get_absolute_url(self):
        return reverse(
            'admin:{}_{}_change'.format(
                self._meta.app_label, self._meta.model_name
            ), args=(self.pk,)
        )


class TaggitTagField(TagField):
    def has_changed(self, initial, data):
        if initial and data:
            initial = set(initial.values_list('tag__name', flat=True))
            data = set([i.strip() for i in data.split(',')])
            compare = len(initial) == len(data) and initial - data

            return compare
        return False


class TaggitTaggableManager(TaggableManager):

    def formfield(self, form_class=TaggitTagField, **kwargs):
        return super().formfield(form_class, **kwargs)


class TaggableMixin(models.Model):
    tags = TaggitTaggableManager(blank=True)

    class Meta:
        abstract = True
