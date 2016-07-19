from django.db import models

from ralph.cross_validator.ralph2 import generate_meta


class DHCPEntry(models.Model):
    mac = models.CharField(max_length=32)
    ip = models.CharField(max_length=len('xxx.xxx.xxx.xxx'))

    class Meta(generate_meta(app_label='dnsedit', model_name='dhcpentry')):
        pass
