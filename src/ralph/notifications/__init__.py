# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import django_rq

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from ralph.notifications.models import Notification
from ralph.notifications.conf import NOTIFICATIONS_QUEUE_NAME


class SendingError(Exception):
    """Exception during send mail task."""


def send_email_notification(notification_id):
    try:
        notification = Notification.objects.get(
            sent=False,
            pk=notification_id,
        )
    except Notification.DoesNotExist:
        return
    msg = EmailMultiAlternatives(
        notification.subject,
        notification.content_text,
        notification.from_mail,
        [notification.to_mail],
    )
    msg.attach_alternative(notification.content_html, 'text/html')
    if msg.send(True):
        notification.sent = True
    notification.save()
    if not notification.sent:
        raise SendingError('Send failed.')


def send_email(
    receivers,
    sender,
    subject,
    html_template,
    txt_template=None,
    variables={},
    remarks=None,
):
    html_content = render_to_string(
        'notifications/emails/html/%s' % html_template,
        variables,
    )
    if txt_template:
        txt_content = render_to_string(
            'notifications/emails/txt/%s' % txt_template,
            variables,
        )
    else:
        txt_content = strip_tags(html_content)
    if not all((
        not hasattr(receivers, 'strip'),
        hasattr(receivers, '__iter__'),
    )):
        receivers = [receivers]
    for receiver in receivers:
        notification = Notification.objects.create(
            from_mail=sender,
            to_mail=receiver,
            subject=subject,
            content_text=txt_content,
            content_html=html_content,
            remarks=remarks,
        )
        queue = django_rq.get_queue(name=NOTIFICATIONS_QUEUE_NAME)
        job = queue.enqueue_call(
            func=send_email_notification,
            kwargs={
                'notification_id': notification.id,
            },
            timeout=120,
            result_ttl=120,
        )
        job.meta['attempt'] = 1
        job.save()
