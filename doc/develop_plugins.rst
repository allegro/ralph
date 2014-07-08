.. _develop_plugins:

===========================
Writing custom SCAN plugins
===========================

PUSH - REST API interface
-------------------------
The easiest way is to push some data using your favorite tool/language throug the API. Ralph Core will force you to accept the changes before saving.

Benefits:
 - use any language you want
 - can store plugins outside of Ralph Core system
 - more compatibility across new Ralph releases
 - PUSH mode


Quick start - PUSH
------------------
Let's write the easiest SCAN PUSH plugin. For example, you wan't to list hypervisor machines and register them with the Ralph interface.

To do this you have to:

1. Obtain API Key from the Ralph interface - on the bottom part of the page you will see your login name (preference) click on it, and choose "Api key". You will see your api key there.
2. Prepare your script which generate JSON data. You have to use following schema::

For example file /tmp/data.json ::

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



2. Send JSON data to the API interface using your script(REST call), or via commandline like this:


curl -XPOST https://ralph.office/api/v0.9/scanresult/ -d @/tmp/data.json -H "Authorization: ApiKey user.name:api_key" -H "Content-type: application/json"

3. View & accept your data using GUI: you can use direct URL pasting your IP Address into the URL  http://ralph.address/ui/scan/status/127.0.0.1/ - or just navigate to your IP Address using Networks / Scan tab - you will see 'Full Scan' link.


PULL - Generic SCAN plugins
---------------------------
Use this if your hardware is a generic one, and can be periodically scanned
alongside other existing plugins like http, snmp, ping.

First-class SCAN plugin allows you to reuse some features like:
  - you don't have to reinvent ping scans, snmp scanning
  - Python knowledge required
  - strictly integrated with k

