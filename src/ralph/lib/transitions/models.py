# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db import models


class TransitionConfigModel(models.Model):
    name = models.CharField('name', max_length=50)
    content_type = models.ForeignKey(ContentType)
    field_name = models.CharField('field name', max_length=50)
    source = models.PositiveIntegerField('source', blank=True, null=True)
    target = models.PositiveIntegerField('target')
    actions = models.CharField('actions', max_length=150)
