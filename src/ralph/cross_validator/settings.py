# -*- coding: utf-8 -*-
import json
import os

from ralph.settings.base import *

DEBUG = True

DATABASES.update({
    'ralph2': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('RALPH2_DATABASE_NAME', 'ralph_2'),
        'USER': os.environ.get('RALPH2_DATABASE_USER', 'root'),
        'PASSWORD': os.environ.get('RALPH2_DATABASE_PASSWORD', 'mysql') or None,
        'HOST': os.environ.get('RALPH2_DATABASE_HOST', '127.0.0.1'),
        'PORT': os.environ.get('RALPH2_DATABASE_PORT', 3306),
    },
    'ralph3': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('RALPH3_DATABASE_NAME', 'ralph_3'),
        'USER': os.environ.get('RALPH3_DATABASE_USER', 'root'),
        'PASSWORD': os.environ.get('RALPH3_DATABASE_PASSWORD', 'mysql') or None,
        'HOST': os.environ.get('RALPH3_DATABASE_HOST', '127.0.0.1'),
        'PORT': os.environ.get('RALPH3_DATABASE_PORT', 3306),
    }
})

DATABASE_ROUTERS = ['ralph.cross_validator.db_routers.CrossRouter']
