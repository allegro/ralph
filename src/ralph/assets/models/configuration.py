# -*- coding: utf-8 -*-

from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.models import MPTTModel, MPTTModelBase, TreeForeignKey

from ralph.assets.models.base import BaseObject
from ralph.lib.custom_fields.models import (
    CustomFieldMeta,
    WithCustomFieldsMixin
)
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin

dir_file_name_validator = RegexValidator(regex=r"\w+")

ConfigurationModuleBase = type(
    "ConfigurationModuleBase", (MPTTModelBase, CustomFieldMeta), {}
)


class ConfigurationModule(
    WithCustomFieldsMixin,
    AdminAbsoluteUrlMixin,
    MPTTModel,
    TimeStampMixin,
    models.Model,
    metaclass=ConfigurationModuleBase,
):
    name = models.CharField(
        verbose_name=_("name"),
        max_length=255,
        help_text=_("module name (ex. directory name in puppet)"),
        validators=[dir_file_name_validator],
    )
    parent = TreeForeignKey(
        "self",
        verbose_name=_("parent module"),
        null=True,
        blank=True,
        default=None,
        related_name="children_modules",
        on_delete=models.CASCADE,
    )
    # TODO: is this necessary?
    support_team = models.ForeignKey(
        "accounts.Team",
        verbose_name=_("team"),
        null=True,
        blank=True,
        default=None,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("configuration module")
        unique_together = ("parent", "name")
        ordering = ("parent__name", "name")

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # update children classes
        for cls in self.configuration_classes.all():
            cls.save()


class ConfigurationClass(AdminAbsoluteUrlMixin, BaseObject):
    class_name = models.CharField(
        verbose_name=_("class name"),
        max_length=255,
        help_text=_("ex. puppet class"),
        validators=[dir_file_name_validator],
    )
    path = models.CharField(
        verbose_name=_("path"),
        blank=True,
        default="",
        editable=False,
        max_length=511,  # 255 form module name, '/' and 255 from class name
        help_text=_("path is constructed from name of module and name of class"),
    )
    module = models.ForeignKey(
        ConfigurationModule,
        related_name="configuration_classes",
        on_delete=models.CASCADE,
    )

    autocomplete_words_split = True

    class Meta:
        verbose_name = _("configuration class")
        unique_together = ("module", "class_name")
        ordering = ("path",)

    def __str__(self):
        return self.path

    def save(self, *args, **kwargs):
        self.path = self.module.name + "/" + self.class_name
        super().save(*args, **kwargs)
