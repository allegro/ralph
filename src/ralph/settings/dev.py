# flake8: noqa: E405
from ralph.settings import *  # noqa


def only_true(request):
    '''For django debug toolbar.'''
    return True

DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + (  # type: ignore
    'debug_toolbar',
    'django_extensions',
)

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + (  # type: ignore
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': "%s.only_true" % __name__,
}

ROOT_URLCONF = 'ralph.urls.dev'

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
        },
    },
]

LOGGING['handlers']['console']['level'] = 'DEBUG'  # type: ignore
for logger in LOGGING['loggers']:  # type: ignore
    LOGGING['loggers'][logger]['level'] = 'DEBUG'  # type: ignore
    LOGGING['loggers'][logger]['handlers'].append('console')  # type: ignore

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

ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['RETURN_TRANSITION_ID'] = 1
ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['LOAN_TRANSITION_ID'] = 1
ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['TRANSITION_ID'] = 1
