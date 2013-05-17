#
# A testing profile.
#
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {},
    }
}
if not 'ralph_assets' in INSTALLED_APPS:
    INSTALLED_APPS.append('ralph_assets')
INSTALLED_APPS.append('ralph_pricing')
