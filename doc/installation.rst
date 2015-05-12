Installation
============

Installation requirements:

    1. Install Ralph .

Asset installation:

    1. Install the ``ralph_assets`` package from PyPi by running::

        pip install ralph_assets


    2. After installation add a line in settings ::


        PLUGGABLE_APPS = ['assets',]

    3. Run::

        ralph migrate ralph_assets


That's it. Now just run Ralph as described in its documentation, and login to
the Ralph system.  You will see an additional item, "Assets" in the main menu.
