# Ralph development environment

    Disclaimer #1:
    This document describes an easy to set up development environment for Ralph.
    It should be considered as the only possible option. Every individual may
    have their own environment configured in their own way.

    Disclaimer #2:
    This guide assumes the host platform runs a POSIX-compliant environment and
    provides a POSIX-compliant command intrepreter.

## Requirements

Make sure your host has the following requirements installed and
properly configured, if required:

1.  Python 3.5 or later
1.  pip
1.  virtualenvwrapper
1.  NodeJS
1.  npm
1.  Docker 1.13.0 or later
1.  docker-compose

If you are a Ralph maintainer, make sure you have [Maintainer's development tools][1]
installed as well.


## Setting up Ralph

Ralph is a Django base application that uses several third-party modules.
Therefore it depends on many external Python packages that have to be installed
to one of the interpreter's paths for package resolution. It is recommended to
use a Python virtual environment to avoid conflicts and other issues.

To set up Ralph follow the following steps:

1. Obtain source code of Ralph.
1. Change current working directory within your terminal session to where the
source code is.
1. Create a virtual environment by running
        ```
        $ mkvirtualenv -p "$(which python3)" ralph
        ```
The environment will be activated upon creation.
1. Install required python packages
        ```
        $ pip install -r requirements/dev.txt
        ```
Please note, it may be necessary to install appropriate shared libraries and
build tools in order for some python packages to be built.
1. Install JS requirements and build static files
        ```
        $ npm install
        ```
1. Build static files. Depending on your platform ```gulp``` executable
may be found in either node_modules/.bin/ or node_modules/bin/ catalogues:
        ```
        $ ./node_modules/.bin/gulp || ./node_modules/bin/gulp
        ```
Please note, it is necessary to perform this step every
time static files are changed.


## Running required services

It is possible to run all required services, i. e., database, cache, etc in
Docker containers using [prepared compose file][2]. It is available in the
source tree under ```docker/docker-compose-dev.yml``` path so the services
can be started with the following command:

```bash
$ docker-compose -f docker/docker-compose-dev.yml up -d
```

Both mysql and redis containers will map appropriate ports to the local
interface. the ```volumes``` catalogue will contain all mounted volumes for
launched containers. A database called ralph_ng will be created automatically.
A user called ralph_ng having a password that matches its username will be
created and granted permissions to that DB as well.


## Configuration and running

Create a file called ```local.py``` in ```src/ralph/settings/``` and place the
following content inside:

```python
from ralph.settings.dev import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'transaction_hooks.backends.mysql',
        'NAME': os.environ.get('DATABASE_NAME', 'ralph_ng'),
        'USER': os.environ.get('DATABASE_USER', 'ralph_ng'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'ralph_ng') or None,
        'HOST': os.environ.get('DATABASE_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DATABASE_PORT', 3306),
        'ATOMIC_REQUESTS': True,
        'TEST': {
            'NAME': 'test_ralph_ng',
            'ENGINE': 'transaction_hooks.backends.postgresql_psycopg2',
            'USER': os.environ.get('DATABASE_USER', 'ralph_ng'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'ralph_ng') or None,
            'HOST': os.environ.get('DATABASE_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DATABASE_PORT', 3306),
        }
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ENABLE_EMAIL_NOTIFICATION = True
```

Next point ```DJANGO_SETTINGS_MODULE``` environment variable to that
configuration module:

```bash
$ export DJANGO_SETTINGS_MODULE="ralph.settings.local"
```

It is now possible to run Ralph in development mode:

```bash
$ python setup.py develop
$ dev_ralph migrate
$ dev_ralph createsuperuser
$ make menu
$ dev_ralph runserver_plus 0.0.0.0:8000
```

At this point Ralph should be available under http://127.0.0.1:8000. As soon as
the script detects any changes in the source code the server will be restarted
automatically.


[1]: ./maintainers_devtools.md
[2]: https://raw.githubusercontent.com/allegro/ralph/ng/docker/docker-compose-dev.yml
