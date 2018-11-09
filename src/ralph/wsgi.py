"""
WSGI config for ralph project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

## Loading WSGI environment variables into the django application:
## https://exceptionshub.com/access-apache-setenv-variable-from-django-wsgi-py-file.html

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ralph.settings")

KEYS_TO_LOAD = [
    # A list of the keys you'd like to load from the WSGI environ
    # into os.environ
	'DATABASE_HOST',
	'DATABASE_USER',
	'DATABASE_NAME',
	'DATABASE_PASSWORD'
]

def loading_app(wsgi_environ, start_response):
    global real_app
    for key in KEYS_TO_LOAD:
        try:
            os.environ[key] = wsgi_environ[key]
        except KeyError:
            # The WSGI environment doesn't have the key
            pass
    real_app = get_wsgi_application()
    return real_app(wsgi_environ, start_response)

real_app = loading_app

application = lambda env, start: real_app(env, start)
