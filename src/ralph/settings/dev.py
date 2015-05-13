from ralph.settings import *  # noqa


def only_true(request):
    '''For django debug toolbar.'''
    return True

DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + (
    'debug_toolbar',
    'django_extensions',
)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': "%s.only_true" % __name__,
}

ROOT_URLCONF = 'ralph.urls.dev'
