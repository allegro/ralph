from dj.choices import Choices

from django.db import models

from ralph.cross_validator.ralph2 import generate_meta


class CI_STATE_TYPES(Choices):
    _ = Choices.Choice

    ACTIVE = _('Active')
    INACTIVE = _('Inactive')
    WAITING = _('Waiting for deactivation')


class CI_TYPES(Choices):
    _ = Choices.Choice

    APPLICATION = _('Application')
    DEVICE = _('Device')
    PROCEDURE = _('Procedure')
    VENTURE = _('Venture')
    VENTUREROLE = _('Venture Role')
    BUSINESSLINE = _('Business Line')
    SERVICE = _('Service')
    NETWORK = _('Network')
    DATACENTER = _('Data Center')
    NETWORKTERMINATOR = _('Network Terminator')
    ENVIRONMENT = _('Environment')
    PROFIT_CENTER = _('Profit Center')


class CI(models.Model):
    uid = models.CharField(max_length=100)
    name = models.CharField(max_length=256)

    class Meta(generate_meta(app_label='cmdb', model_name='ci')):
        pass
