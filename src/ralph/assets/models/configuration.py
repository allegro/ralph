# -*- coding: utf-8 -*-

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey

from ralph.lib.mixins.models import TimeStampMixin


dir_file_name_validator = RegexValidator(regex='\w+')


class ConfigurationModule(MPTTModel, TimeStampMixin, models.Model):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=255,
        help_text=_('module name (ex. directory name in puppet)'),
        validators=[dir_file_name_validator],
    )
    parent = TreeForeignKey(
        'self',
        verbose_name=_('parent venture'),
        null=True,
        blank=True,
        default=None,
        related_name='child_set',
    )
    path = models.TextField(
        verbose_name=_('path'),
        blank=True,
        default='',
        editable=False,
        help_text=_('path is constructed from names of modules in hierarchy')
    )
    # TODO: is this necessary?
    support_team = models.ForeignKey(
        'accounts.Team',
        verbose_name=_('team'),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _('configuration module')
        unique_together = ('parent', 'name')
        ordering = ('parent__name', 'name')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        if self.parent:
            self.path = self.parent.path + '/' + self.name
        else:
            self.path = self.name
        super().save(*args, **kwargs)
        # update children paths
        for child in self.child_set.all():
            child.save()
        # update children classes
        for cls in self.configuration_classes.all():
            cls.save()


class ConfigurationClass(TimeStampMixin, models.Model):
    name = models.CharField(
        verbose_name=_('name'),
        max_length=255,
        help_text=_('class name (ex. file name in puppet)'),
        validators=[dir_file_name_validator],
    )
    path = models.TextField(
        verbose_name=_('path'),
        blank=True,
        default='',
        editable=False,
        help_text=_('path is constructed from names of modules in hierarchy')
    )
    module = models.ForeignKey(
        ConfigurationModule,
        related_name='configuration_classes'
    )

    class Meta:
        verbose_name = _('configuration class')
        unique_together = ('module', 'name')

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.module.path + '/' + self.name
        super().save(*args, **kwargs)
