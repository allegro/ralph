# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db import models


class TransitionConfigModel(models.Model):
    name = models.CharField('name', max_length=50)
    content_type = models.ForeignKey(ContentType)
    field_name = models.CharField('field name', max_length=50)
    source = models.CharField('source', max_length=50, default='*')
    target = models.CharField('target', max_length=50)
    actions = models.CharField('actions', max_length=150)
