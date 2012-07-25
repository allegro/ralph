.. _configuration:

=============
Configuration
=============

Configuration file layout
-------------------------

Ralph is a Django-based project. As such, in its sources it holds a default
configuration file called ``settings.py``. This file should not be touched as it
can change between Ralph versions. Instead, you can place your configuration in:

 - ``settings-local.py`` (next to ``settings.py`` in the source package)

 - ``~/.ralph/settings``

 - ``/etc/ralph/settings``

Upon starting, Ralph will search those paths in the order specified above and
stick to the first file it finds. Configuration in this file overrides defaults
provided in ``settings.py``.

Settings files are in their essence Python source code files. You can consult
`official Django documentation
<https://docs.djangoproject.com/en/1.4/ref/settings/#databases>`_ on various
ways you can customize behaviour of the application.

Creating a default configuration file
-------------------------------------

A default configuration file can be created by invoking::

  (ralph)$ ralph makeconf

This will create the ``~/.ralph/settings`` file with default values. Ralph will
not overwrite existing configuration, you can change that by adding ``--force``
to ``makeconf``.

You can also create your configuration in ``/etc`` by adding ``--global`` to
``makeconf``.

.. warning::  

   The ``settings`` file will contain passwords and other sensitive information.
   Therefore by default ``makeconf`` ensures your configuration directory as
   well as the ``settings`` file are only accessible by the current user
   invoking ``makeconf``.

Secret key
----------

The single most important setting you have to change right away is the
:index:`SECRET_KEY` value. It is used as a seed in secret-key hashing
algorithms, for instance for user passwords and form protection. Each of your
Ralph installations should have its own unique secret key. As for its value, the
longer the better.

Database backend
----------------

To change the default SQLite database backend to another one, you need to edit
the :index:`DATABASES` dictionary. For the complete set of options check `the
official Django docs
<https://docs.djangoproject.com/en/1.4/ref/settings/#databases>`_. For example,
setting up MySQL could look like this::

  DATABASES = {
    'default': {
       'ENGINE': 'django.db.backends.mysql',
       'NAME': 'ralph_db',
       'USER': 'ralph_user',
       'PASSWORD': 'ralph_password',
       'HOST': '127.0.0.1',
       'PORT': '3306',
       'OPTIONS': {
          "init_command": "SET storage_engine=INNODB",
       },
    },
  }

Message queue broker
--------------------

To change the default SQLite message broker to another one, you need to edit the
:index:`BROKER_URL` setting. For the complete set of options check `the official
Celery docs
<http://docs.celeryproject.org/en/latest/getting-started/brokers/index.html>`_.
For example, setting up Redis could look like this::

  BROKER_URL = "redis://127.0.0.1:6379/4"

.. note::

  For Redis support you will also need to install a connector library. Simply
  type::

    $ pip install redis

Cache
-----

To change the default in-memory cache to Memcached, change the default cache's
backend from ``LocMemCache`` to ``MemcachedCache`` and specify its location,
i.e. ``127.0.0.1:11211``. You can also use Unix sockets and share cache over
multiple servers. Consult `the official Django docs
<https://docs.djangoproject.com/en/dev/topics/cache/?from=olddocs/#memcached>`_.
