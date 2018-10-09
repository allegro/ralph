from collections import namedtuple

EmailContext = namedtuple('EmailContext', 'subject body')


def get_email_context_for_transition(transition) -> EmailContext:
    default = {
        'subject': 'Documents for {}'.format(transition.name),
        'body': 'Please see documents provided in attachments for "{}".'.format(transition.name)  # noqa
    }
    return EmailContext(**default)
