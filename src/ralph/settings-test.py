#
# A testing profile. 
#
SECRET_KEY = 'Ralph--remember what we came for. The fire. My specs.'
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DUMMY_SEND_MAIL = DEBUG
SEND_BROKEN_LINK_EMAILS = DEBUG
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
LOGGING['handlers']['file']['filename'] = CURRENT_DIR + 'runtime.log'
BROKER_HOST = "localhost"
BROKER_PORT = 25672
BROKER_USER = "ralph"
BROKER_PASSWORD = "ralph"
BROKER_VHOST = "/ralph"

