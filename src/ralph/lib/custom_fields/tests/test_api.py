# -*- coding: utf-8 -*-
from ddt import data, ddt, unpack
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import SomeModel


class CustomFieldsAPITests(APITestCase):
    pass
