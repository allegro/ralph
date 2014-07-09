===================
Ralph Windows Agent
===================

To discover Windows based machines, we provide Agent called ``Don Pedro`` for hardware discovery. It requires only .NET 2.0 environment installed, and support Virtual Machines as well.

Installation
------------

1. Download DonPedro windows client: http://ralph.allegrogroup.com/donpedro.msi and install it on the target windows device.
2. You need to configure it. After installation, new service called `Don Pedro` will register in the windows services console. It is enabled by default, and will log message about missing configuration file options. This file usually is located in  c:/Program Files/DonPedro and is called DonPedro.exe.config.
3. Edit configuration file and restart service. It will send information to the given ``ralph_url``, using ``api_user`` and ``api_key`` periodically.