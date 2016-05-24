from dj.choices import Choices
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.lib.mixins.models import NamedMixin


class PrebootFileType(Choices):
    _ = Choices.Choice

    LINUX = Choices.Group(0)
    kernel = _('kernel')
    initrd = _('initrd')

    CONFIGURATION = Choices.Group(40)
    boot_ipxe = _('boot_ipxe')
    kickstart = _('kickstart')

    OTHER = Choices.Group(100)
    other = _('other')


class PrebootFile(NamedMixin):
    type = models.PositiveIntegerField(
        verbose_name=_('type'), choices=PrebootFileType(),
        default=PrebootFileType.other.id,
    )
    raw_config = models.TextField(
        _('raw config'),
        blank=True,
        help_text=_(
            'All newline characters will be converted to Unix \\n '
            'newlines. You can use {{variables}} in the body. '
            'Available variables: filename, filetype, mac, ip, '
            'hostname, venture and venture_role.'
        ),
    )
    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = _('preboot file')
        verbose_name_plural = _('preboot files')


class Preboot(NamedMixin):
    files = models.ManyToManyField(
        PrebootFile,
        blank=True,
        verbose_name=_('files'),
    )
    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = _('preboot')
        verbose_name_plural = _('preboots')
        ordering = ('name',)
