# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.db import models as db
from django.utils.translation import ugettext_lazy as _


class Notification(db.Model):
    from_mail = db.EmailField(
        verbose_name=_('sender'),
        max_length=254,
    )
    to_mail = db.EmailField(
        verbose_name=_('receiver'),
        max_length=254,
    )
    subject = db.CharField(
        verbose_name=_('subject'),
        max_length=254,
    )
    content_text = db.TextField(
        verbose_name=_('content (txt)'),
    )
    content_html = db.TextField(
        verbose_name=_('content (html)'),
    )
    created = db.DateTimeField(
        verbose_name=_('created at'),
        auto_now=False,
        auto_now_add=True,
    )
    sent = db.BooleanField(
        verbose_name=_('sent'),
        default=False,
        db_index=True,
    )
    remarks = db.TextField(
        verbose_name=_('remarks'),
        null=True,
        blank=True,
    )
