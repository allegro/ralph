from django.db import models

from ..fields import MACAddressField


class MACModel(models.Model):
    mac = MACAddressField()
