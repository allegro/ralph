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

# Disable exception for the missing element in SiteTree
# https://github.com/idlesign/django-sitetree/pull/157/files
RAISE_ITEMS_ERRORS_ON_DEBUG = False

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'ralph.lib.template.loaders.AppTemplateLoader',
            ],
            'string_if_invalid': TEMPLATE_STRING_IF_INVALID
        },
    },
]

LOGGING['handlers']['console']['level'] = 'DEBUG'
for logger in LOGGING['loggers']:
    LOGGING['loggers'][logger]['level'] = 'DEBUG'
    LOGGING['loggers'][logger]['handlers'].append('console')

if bool_from_env('RALPH_PROFILING'):
    SILKY_PYTHON_PROFILER = True
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (
        'silk.middleware.SilkyMiddleware',
    )
    INSTALLED_APPS = INSTALLED_APPS + (
        'silk',
    )
    SILKY_DYNAMIC_PROFILING = [
        {
            'module': 'ralph.data_center.admin',
            'function': 'DataCenterAssetAdmin.changelist_view'
        },
    ]
