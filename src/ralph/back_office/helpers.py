from collections import namedtuple

EmailContext = namedtuple('EmailContext', 'subject body')


def get_email_context_for_transition(transition_name: str) -> EmailContext:
    """Default method used in action (send_attachments_to_user)."""
    default = {
        'subject': 'Documents for {}'.format(transition_name),
        'body': 'Please see documents provided in attachments for "{}".'.format(transition_name)  # noqa
    }
    return EmailContext(**default)
