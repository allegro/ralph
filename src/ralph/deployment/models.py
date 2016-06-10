import os

from dj.choices import Choices
from django.db import models
from django.db.models import F
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import Ethernet
from ralph.lib.external_services.models import JobManager
from ralph.lib.mixins.models import NamedMixin
from ralph.lib.polymorphic.models import Polymorphic, PolymorphicBase
from ralph.lib.transitions.models import (
    TransitionJob,
    TransitionJobActionStatus
)


class PrebootItemType(Choices):
    _ = Choices.Choice

    LINUX = Choices.Group(0)
    kernel = _('kernel')
    initrd = _('initrd')

    CONFIGURATION = Choices.Group(40)
    ipxe = _('iPXE')
    kickstart = _('kickstart')

    OTHER = Choices.Group(100)
    other = _('other')


def get_choices_from_group(choices_group):
    return (
        (choice.id, choice.name) for choice in choices_group.choices
    )


def preboot_file_name(instance, filename):
    return os.sep.join(
        ('pxe', instance.get_type_display(), slugify(instance.name))
    )


class PrebootItem(NamedMixin, Polymorphic, metaclass=PolymorphicBase):
    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
        default='',
    )

    @property
    def autocomplete_str(self):
        return '<i>{}</i> {}'.format(self.get_type_display(), self.name)


class PrebootConfiguration(PrebootItem):
    type = models.PositiveIntegerField(
        verbose_name=_('type'),
        choices=get_choices_from_group(PrebootItemType.CONFIGURATION),
        default=PrebootItemType.ipxe.id,
    )
    configuration = models.TextField(
        _('configuration'),
        blank=True,
        help_text=_(
            'All newline characters will be converted to Unix \\n '
            'newlines. You can use {{variables}} in the body. '
            'Available variables: ralph_instance, deployment_id, kickstart, '
            'initrd, kernel, dc, done_url.'
        ),
    )

    class Meta:
        verbose_name = _('preboot configuration')
        verbose_name_plural = _('preboot configuration')

    def __str__(self):
        return '{} - {}'.format(self.name, self.get_type_display())


class PrebootFile(PrebootItem):
    type = models.PositiveIntegerField(
        verbose_name=_('type'),
        choices=get_choices_from_group(PrebootItemType.LINUX),
        default=PrebootItemType.kernel.id,
    )
    file = models.FileField(
        _('file'),
        upload_to=preboot_file_name,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = _('preboot file')
        verbose_name_plural = _('preboot files')


class Preboot(NamedMixin):
    items = models.ManyToManyField(
        PrebootItem,
        blank=True,
        verbose_name=_('files'),
    )
    description = models.TextField(
        verbose_name=_('description'),
        blank=True,
        default='',
    )

    used_counter = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = _('preboot')
        verbose_name_plural = _('preboots')
        ordering = ('name',)

    def increment_used_counter(self):
        self.used_counter = F('used_counter') + 1
        self.save()

    def _get_item(self, model_name, item_type):
        item = None
        try:
            queryset_kwargs = {
                '{}__type'.format(model_name): PrebootItemType.id_from_name(item_type)  # noqa
            }
            item = self.items.get(**queryset_kwargs)
        except PrebootItem.DoesNotExist:
            pass
        return item

    def get_file_url(self, file_type):
        item = self._get_item(model_name='prebootfile', item_type=file_type)
        if item is not None and item.file:
            return item.file.url

    def get_configuration(self, configuration_type):
        item = self._get_item(
            model_name='prebootconfiguration',
            item_type=configuration_type
        )
        if item is not None:
            return item.configuration


class DeploymentManager(JobManager):
    def get_queryset(self):
        from ralph.deployment.deployment import deploy
        # TODO: test it
        return super().get_queryset().filter(
            transition__actions__name=deploy.__name__
        )


class Deployment(TransitionJob):
    objects = DeploymentManager()

    class Meta:
        proxy = True

    @classmethod
    def get_deployment_for_ip(cls, ip):
        base_object = Ethernet.objects.get(ipaddress__address=ip).base_object
        return cls.objects.active().get(
            content_type_id=base_object.content_type_id,
            object_id=base_object.id
        )

    @property
    def preboot(self):
        return self.params['data']['deploy__preboot']

    @classmethod
    def mark_as_done(cls, deployment_id):
        deployment = cls.objects.get(id=deployment_id)
        tja = deployment.transition_job_actions.get(
            action_name='wait_for_ping'
        )
        tja.status = TransitionJobActionStatus.FINISHED
        tja.save()
