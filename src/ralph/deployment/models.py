import logging
import os

from dj.choices import Choices
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.db.models.manager import Manager
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import Ethernet
from ralph.lib.external_services.models import JobQuerySet
from ralph.lib.mixins.fields import NUMP
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, NamedMixin
from ralph.lib.polymorphic.fields import PolymorphicManyToManyField
from ralph.lib.polymorphic.models import Polymorphic, PolymorphicBase
from ralph.lib.transitions.models import TransitionJob

logger = logging.getLogger(__name__)


class PrebootItemType(Choices):
    _ = Choices.Choice

    LINUX = Choices.Group(0)
    kernel = _("kernel")
    initrd = _("initrd")
    netboot = _("netboot")

    CONFIGURATION = Choices.Group(40)
    ipxe = _("iPXE")
    kickstart = _("kickstart")
    preseed = _("preseed")
    script = _("script")
    meta_data = _("meta-data")
    user_data = _("user-data")

    OTHER = Choices.Group(100)
    other = _("other")


def get_choices_from_group(choices_group):
    return ((choice.id, choice.name) for choice in choices_group.choices)


def preboot_file_name(instance, filename):
    return os.sep.join(("pxe", instance.get_type_display(), slugify(instance.name)))


class PrebootItem(
    AdminAbsoluteUrlMixin, NamedMixin, Polymorphic, metaclass=PolymorphicBase
):
    description = models.TextField(
        verbose_name=_("description"),
        blank=True,
        default="",
    )

    @property
    def autocomplete_str(self):
        return "<i>{}</i> {}".format(self.get_type_display(), self.name)


CONFIGURATION_HELP_TEXT = """
All newline characters will be converted to Unix \\n newlines.
<br>You can use {{{{variables}}}} in the body.
<br>Available variables:

<br>  - configuration_class_name (eg. 'www')
<br>  - configuration_module (eg. 'ralph')
<br>  - configuration_path (eg. 'ralph/www')
<br>  - dc (eg. 'data-center1')
<br>  - deployment_id (eg. 'ea9ea3a0-1c4d-42b7-a19b-922000abe9f7')
<br>  - domain (eg. 'dc1.mydc.net')
<br>  - done_url (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/mark_as_done')
<br>  - hostname (eg. 'ralph123.dc1.mydc.net')
<br>  - initrd (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/initrd')
<br>  - kernel (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/kernel')
<br>  - netboot (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/netboot')
<br>  - kickstart (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/kickstart')
<br>  - preseed (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/preseed')
<br>  - meta_data (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/meta-data')
<br>  - user_data (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/user-data')
<br>  - deployment_base (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/')
<br>  - script (eg. '{ralph_instance}/deployment/ea9ea3a0-1c4d-42b7-a19b-922000abe9f7/script')
<br>  - ralph_instance (eg. '{ralph_instance}')
<br>  - service_env (eg. 'Backup systems - prod')
<br>  - service_uid (eg. 'sc-123')
""".format(ralph_instance=settings.RALPH_INSTANCE.rstrip("/")).strip()  # noqa


class PrebootConfiguration(PrebootItem):
    type = models.PositiveIntegerField(
        verbose_name=_("type"),
        choices=get_choices_from_group(PrebootItemType.CONFIGURATION),
        default=PrebootItemType.ipxe.id,
    )
    configuration = NUMP(
        models.TextField(
            _("configuration"), blank=True, help_text=_(CONFIGURATION_HELP_TEXT)
        )
    )

    class Meta:
        verbose_name = _("preboot configuration")
        verbose_name_plural = _("preboot configuration")

    def __str__(self):
        return "{} - {}".format(self.name, self.get_type_display())


class PrebootFile(PrebootItem):
    type = models.PositiveIntegerField(
        verbose_name=_("type"),
        choices=get_choices_from_group(PrebootItemType.LINUX),
        default=PrebootItemType.kernel.id,
    )
    file = models.FileField(
        _("file"),
        upload_to=preboot_file_name,
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = _("preboot file")
        verbose_name_plural = _("preboot files")


class ActiveObjectsManager(Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(disappears_after__isnull=True)
                | Q(disappears_after__gte=timezone.now())
            )
        )


class Preboot(AdminAbsoluteUrlMixin, NamedMixin):
    objects = Manager()
    active_objects = ActiveObjectsManager()

    items = PolymorphicManyToManyField(
        PrebootItem,
        blank=True,
        verbose_name=_("files"),
    )
    description = models.TextField(
        verbose_name=_("description"),
        blank=True,
        default="",
    )
    warning_after = models.DateField(null=True, blank=False)
    critical_after = models.DateField(null=True, blank=False)
    disappears_after = models.DateField(null=True, blank=False)

    used_counter = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        verbose_name = _("preboot")
        verbose_name_plural = _("preboots")
        ordering = ("name",)

    def increment_used_counter(self):
        self.used_counter = F("used_counter") + 1
        self.save()

    def _get_item(self, model_name, item_type):
        item = None
        try:
            queryset_kwargs = {
                "{}__type".format(model_name): PrebootItemType.id_from_name(item_type)  # noqa
            }
            item = self.items.get(**queryset_kwargs)
        except PrebootItem.DoesNotExist:
            pass
        return item

    def get_file_url(self, file_type):
        item = self._get_item(model_name="prebootfile", item_type=file_type)
        if item is not None and item.file:
            return item.file.url

    def get_configuration(self, configuration_type):
        item = self._get_item(
            model_name="prebootconfiguration", item_type=configuration_type
        )
        if item is not None:
            return item.configuration


class DeploymentManager(Manager.from_queryset(JobQuerySet)):
    def get_queryset(self):
        from ralph.deployment.deployment import deploy

        # TODO: test it
        return super().get_queryset().filter(transition__actions__name=deploy.__name__)


class Deployment(AdminAbsoluteUrlMixin, TransitionJob):
    objects = DeploymentManager()

    class Meta:
        proxy = True

    @classmethod
    def get_deployment_for_ip(cls, ip):
        base_object = Ethernet.objects.get(ipaddress__address=ip).base_object
        return cls.objects.active().get(
            content_type_id=base_object.content_type_id, object_id=base_object.id
        )

    @property
    def preboot(self):
        return self.params["data"]["deploy__preboot"]

    @classmethod
    def mark_as_done(cls, deployment_id):
        deployment = cls.objects.get(id=deployment_id)
        if deployment.is_frozen:
            deployment.unfreeze()
        else:
            logger.warning("Deployment %s was already unfrozen", deployment)
