from dj.choices import Choices


class IPAddressStatus(Choices):
    _ = Choices.Choice

    used = _('DHCP (used)')
    reserved = _('reserved').extra(help_text=_('Exclude from DHCP'))
