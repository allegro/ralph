# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from django.contrib import admin

from ralph.notifications.models import Notification


class NotificationBaseAdmin(admin.ModelAdmin):
    list_display = (
        'from_mail', 'to_mail', 'subject', 'created', 'remarks', 'sent',
    )
    fields = (
        'from_mail', 'to_mail', 'subject', 'content_text',
        'content_html', 'remarks', 'sent',
    )
    date_hierarchy = 'created'
    search_fields = ['to_mail', 'to_email', 'subject', 'remarks']
    list_filter = ('sent',)
    readonly_fields = Notification._meta.get_all_field_names()

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Notification, NotificationBaseAdmin)
