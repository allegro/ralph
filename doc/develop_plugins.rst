.. _develop_plugins:

===============
Extending Ralph
===============

Writing custom SCAN plugins
---------------------------

PUSH - REST API interface
*************************
The easiest way is to push some data using your favorite tool/language through the API. Ralph Core will force you to accept the changes before saving.

Benefits:
 - use any language you want
 - can store plugins outside of Ralph Core system
 - more compatibility across new Ralph releases
 - PUSH mode


Let's write the easiest SCAN PUSH plugin. For example, you want to list hypervisor machines and register them with the Ralph interface.

To do this you have to:

1. Obtain an API Key from the Ralph interface - on the bottom part of the page you will see your login name (preference) click on it, and choose "Api key". You will see your api key there.
2. Prepare your script which generates JSON data.

Example file /tmp/data.json ::

    {
        "data": {
            "date": "2014-01-01 01:01:01",
            "device": {
                "disk_shares": [
                ],
                "disks": [
    	            {
                        "family": "XENSRC PVDISK SCSI Disk Device",
                        "label": "XENSRC PVDISK SCSI Disk Device",
                        "mount_point": "\\\\.\\PHYSICALDRIVE0",
                        "serial_number": "ca009e3f-83a3-48",
                        "size": "40607"
                    }
                ],
                "fibrechannel_cards": [
                ],
                "installed_software": [
    	            {
                        "label": "Windows Driver Package - Citrix Systems Inc.",
                        "model_name": "Windows Driver Package - Citrix Systems",
                        "path": "Citrix Systems Inc. - Windows Driver Package",
                        "version": "05/09/2013 7.0.0.86"
                    },

                ],
                "mac_addresses": ["de:ad:be:ef:ca:fe"],
                "memory": [],
                "model_name": [
                    "HP Blade Center XXL"
                ],
                "processors": [
                 {
                        "cores": "1",
                        "family": "Virtual Intel64 Family 6 Model 62 Stepping 4",
                        "index": "CPU0",
                        "label": "Virtual Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz",
                        "model_name": "Virtual Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz 2600Mhz",
                        "speed": "2600"
                    },
                    {
                        "cores": "1",
                        "family": "Virtual Intel64 Family 6 Model 62 Stepping 4",
                        "index": "CPU1",
                        "label": "Virtual Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz",
                        "model_name": "Virtual Intel(R) Xeon(R) CPU E5-2650 v2 @ 2.60GHz 2600Mhz",
                        "speed": "2600"
                    }
                ],
                "results_priority": {
                    "disk_shares": 30,
                    "disks": 30,
                    "fibrechannel_cards": 60,
                    "installed_software": 60,
                    "mac_addresses": 50,
                    "memory": 60,
                    "model_name": 25,
                    "processors": 60,
                    "serial_number": 20,
                    "system_cores_count": 60,
                    "system_ip_addresses": 60,
                    "system_memory": 60,
                    "system_storage": 30
                },
                "serial_number": "JAX1037K0C6",
                "system_cores_count": "8",
                "system_ip_addresses": [
                    "127.0.0.1"
                ],
                "system_memory": "8183",
                "system_storage": "91545"
            },
            "messages": [
                "This is a test"
            ],
            "plugin": "donpedro",
            "status": "success"
        }
    }


2. Send JSON data to the API interface using your script (REST call), or via commandline like this ::

    curl -XPOST https://ralph.office/api/v0.9/scanresult/ -d @/tmp/data.json -H "Authorization: ApiKey user.name:api_key" -H "Content-type: application/json"

3. View & accept your data using GUI: you can use direct URL pasting your IP Address into the URL  ``http://ralph.address/ui/scan/status/127.0.0.1/`` - or just navigate to your IP Address using `Networks / Scan tab` - you will see 'Full Scan' link.


PULL - Generic SCAN plugins
---------------------------
Use this if your hardware is a generic one, and can be periodically scanned
alongside other existing plugins like http, snmp, ping.

First-class SCAN plugin allows you to reuse some features like:
  - you don't have to reinvent the ping scans, snmp scanning, http family discoering
  - but - Python knowledge required :)
  - strictly integrated with existing codebase(we accept pull requests :))
  - see example plugin: https://github.com/allegro/ralph/blob/develop/src/ralph/scan/plugins/hp_oa.py

Create a file in src/ralph/scan/plugins which provides ``scan_address`` function, for example something like this ::

    def scan_address(ip_address, **kwargs):
        snmp_name = (kwargs.get('snmp_name', '') or '').lower()
        if snmp_name and "onboard administrator" not in snmp_name:
            raise NoMatchError('It is not HP OA.')
        if kwargs.get('http_family', '') not in ('Unspecified', 'RomPager', 'HP'):
            raise NoMatchError('It is not HP OA.')
        messages = []
        result = get_base_result_template('hp_oa', messages)
        try:
            device_info = _hp_oa(ip_address)
        except (IncompatibleAnswerError, IncompleteAnswerError) as e:
            messages.append(unicode(e))
            result['status'] = 'error'
        else:
            result['status'] = 'success'
            result['device'] = device_info
        return result

Function should return a dict object with keys:
- ``status``: string ("error", "success")
- ``device``: the same ``data`` subkey as in JSON PUSH interface, e.g { "serial_number" : "sn", "model_name": "test"}

Raise NoMatchError if the plugin didn't match the device you're scanning.

Writing own module
------------------

All Ralph apps(CMDB, Assets, Scrooge) are based on the same engine. There's way to make new custom module extending Ralph functionality. They are pinned to the ralph bar with custom icon.

.. image:: _static/custom_modules-module.png


If you want to make complete new module from scratch, you need to subclass the ``Ralph Module`` class.

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
