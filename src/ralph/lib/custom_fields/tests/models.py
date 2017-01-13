# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db import models

from ..models import WithCustomFieldsMixin


class ModelA(WithCustomFieldsMixin, models.Model):
    pass


class ModelB(WithCustomFieldsMixin, models.Model):
    a = models.ForeignKey(ModelA, null=False)


class SomeModel(WithCustomFieldsMixin, models.Model):
    name = models.CharField(max_length=20)
    b = models.ForeignKey(ModelB, null=True, blank=True)
    custom_fields_inheritance = ['b', 'b__a']

    def get_absolute_url(self):
        return reverse(
            'cf_admin:{}_{}_change'.format(
                self._meta.app_label, self._meta.model_name
            ), args=(self.pk,)
        )

    @classmethod
    def get_add_url(self):
        return reverse('cf_admin:{}_{}_add'.format(
            self._meta.app_label, self._meta.model_name
        ))
