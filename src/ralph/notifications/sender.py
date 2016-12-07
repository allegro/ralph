# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from metrology import Metrology
from threadlocals.threadlocals import get_current_user


@Metrology.timer('notification')
def send_notification_for_model(sender, instance, **kwargs):
    if not getattr(instance, '_handle_post_save', False):
        return
    ServiceEnvironment = sender.service_env.field.related_model
    old_service_env_id = instance._previous_state['service_env_id']
    new_service_env_id = instance.service_env_id
    if old_service_env_id and old_service_env_id != new_service_env_id:
        old_service_env = ServiceEnvironment.objects.get(
            pk=old_service_env_id
        )
        new_service_env = ServiceEnvironment.objects.get(
            pk=new_service_env_id
        )

        owners = []
        for field in ['business_owners', 'technical_owners']:
            owners.extend(list(getattr(old_service_env.service, field).all()))
            owners.extend(list(getattr(new_service_env.service, field).all()))

        emails = [owner.email for owner in owners if owner.email]
        if emails:
            context = {
                'old_service_env': old_service_env,
                'new_service_env': new_service_env,
                'date': timezone.now(),
                'object': instance,
                'user': get_current_user()
            }
            html_content = render_to_string(
                'notifications/html/message.html',
                context
            )
            text_content = render_to_string(
                'notifications/txt/message.txt',
                context
            )
            subject = 'Changes in {}'.format(instance)
            msg = EmailMultiAlternatives(
                subject, text_content, settings.EMAIL_FROM, emails
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
