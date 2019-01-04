from collections import namedtuple

from django.conf import settings

EmailContext = namedtuple('EmailContext', 'from_email subject body')


def get_email_context_for_transition(transition_name: str) -> EmailContext:
    """Default method used in action (send_attachments_to_user)."""
    default = {
        'from_email': settings.EMAIL_FROM,
        'subject': 'Documents for {}'.format(transition_name),
        'body': 'Please see documents provided in attachments for "{}".'.format(transition_name)  # noqa
    }
    return EmailContext(**default)
