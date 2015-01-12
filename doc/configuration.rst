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

We currently only support MySQL backend, though some functionality could work with sqlite backend as well.

Setting up MySQL could look like this::

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

There is a number of Redis queues you need to have. By default they are:

* default - all control tasks go here

* cmdb_* - CMDB related tasks go here

* reports - asynchronous reports from the Web app go here

You should also create an entry for each data center you use. You can use
a separate Redis server for any queue. Use the ``RQ_QUEUES`` dictionary for
that. If you only need to reuse the ``'default'`` Redis instance, add your
queues to ``RQ_QUEUES_LIST``.

Cache
-----

The required CACHE backend is currently `redis-cache` which requires running redis instance::

  CACHES = dict(
       default = dict(
           BACKEND = 'redis_cache.cache.RedisCache',
           LOCATION = 'ralph_redis_master:6379',
           OPTIONS = dict(
               DB=2,
               PASSWORD='ralph666',
               CLIENT_CLASS='redis_cache.client.DefaultClient',
               PARSER_CLASS='redis.connection.HiredisParser',
               PICKLE_VERSION=2,
           ),
           KEY_PREFIX = 'RALPH',
       )
   )


Tracking
--------
To configure your tracking provider, you must put your tracking code into TRACKING_CODE variable in settings for eg. ::

  TRACKING_CODE = """<!-- Piwik -->
  <script type="text/javascript">
    var _paq = _paq || [];
    _paq.push(['trackPageView']);
    _paq.push(['enableLinkTracking']);
    (function() {
      var u=(("https:" == document.location.protocol) ? "https" : "http") + "://your-tracking-domain.local/piwik/";
      _paq.push(['setTrackerUrl', u+'piwik.php']);
      _paq.push(['setSiteId', 66]);
      var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0]; g.type='text/javascript';
      g.defer=true; g.async=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
    })();
  </script>
  <noscript><p><img src="http://your-tracking-domain.local/piwik/piwik.php?idsite=66" style="border:0;" alt="" /></p></noscript>
  <!-- End Piwik Code -->"""
