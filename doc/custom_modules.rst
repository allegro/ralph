Writing own module
====================


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
