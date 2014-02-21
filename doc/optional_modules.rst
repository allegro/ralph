----------------------------------------------------
Optional modules
----------------------------------------------------

Ralph can be installed with optional apps. Currently the following are
released:

* Scrooge https://github.com/allegro/ralph_pricing
* Ralph Assets https://github.com/allegro/ralph_assets/

In order for ralph to include them, you need to add them to your configuration
like this::

    PLUGGABLE_APPS = ['scrooge', 'assets']

You can also create your own ralph plugins. To do this, you need to subclass
the ``Ralph Module`` class.

.. autoclass:: ralph.app.RalphModule
    :members:

If you need any default settings for your app, you can manipulate
``self.settings`` in ``__init__`` of your class.

Then you need to point to your ``RalphModule`` subclass in entry points::

    entry_points={                                                              
        'django.pluggable_app': [                                               
            'assets = ralph_assets.app:Assets',                                 
        ],    
    ]
