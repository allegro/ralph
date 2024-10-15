from django.core.mail import EmailMessage

from ralph.lib.transitions.models import Transition


def send_transition_attachments_to_user(
    requester, transition_id, context_func, **kwargs
):
    if kwargs.get("attachments"):
        transition = Transition.objects.get(pk=transition_id)
        context = context_func(transition_name=transition.name)
        email = EmailMessage(
            subject=context.subject,
            body=context.body,
            from_email=context.from_email,
            to=[requester.email],
        )
        for attachment in kwargs["attachments"]:
            email.attach_file(attachment.file.path)
        email.send()
