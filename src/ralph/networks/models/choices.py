from dj.choices import Choices


class IPAddressStatus(Choices):
    _ = Choices.Choice

    used = _("used (fixed address in DHCP)")
    reserved = _("reserved").extra(help_text=_("Exclude from DHCP"))
