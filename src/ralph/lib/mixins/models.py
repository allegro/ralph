# -*- coding: utf-8 -*-
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djmoney.models.fields import MoneyField
from taggit.managers import TaggableManager as TaggableManagerOriginal
from taggit.managers import _TaggableManager  # noqa

from ralph.lib.mixins.fields import TaggitTagField
from ralph.settings import DEFAULT_CURRENCY_CODE


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
        opts = self._meta
        # support for proxy
        if opts.proxy:
            opts = opts.concrete_model._meta
        return reverse(
            'admin:{}_{}_change'.format(
                opts.app_label, opts.model_name
            ), args=(self.pk,)
        )


class ManagerOfManager(_TaggableManager):
    def set(self, *tags, **kwargs):
        def _flatten(nested_list):
            for item in nested_list:
                if isinstance(item, (list, models.QuerySet)):
                    yield from _flatten(item)
                else:
                    yield item
        flattened_tags = list(_flatten(tags))
        super().set(*flattened_tags, **kwargs)


class TaggableManager(TaggableManagerOriginal):

    def __init__(self, *args, **kwargs):
        super().__init__(manager=ManagerOfManager, *args, **kwargs)
        self.manager.name = 'tags'

    def value_from_object(self, instance):
        """
        Fix to work properly with reversion (or more generally, with
        `django.forms.models.model_to_dict` - TaggableManager is not
        ManyToManyField instance, so this result of this method is dumped
        directly to resulting dict.
        """
        qs = super().value_from_object(instance)
        return list(qs.values_list('tag__name', flat=True))

    def formfield(self, form_class=TaggitTagField, **kwargs):
        return super().formfield(form_class, **kwargs)


class TaggableMixin(models.Model):
    tags = TaggableManager(blank=True)

    class Meta:
        abstract = True


class PreviousStateMixin(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fields = [
            getattr(f, 'attname', None) or f.name
            for f in self._meta.get_fields()
        ]
        self._previous_state = {
            k: v for k, v in self.__dict__.items() if k in fields
        }

    class Meta:
        abstract = True


class PriceMixin(models.Model):
    price = MoneyField(
        max_digits=15, decimal_places=2, null=True, default=0,
        default_currency=DEFAULT_CURRENCY_CODE
    )

    class Meta:
        abstract = True
