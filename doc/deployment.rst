Server deployment
*****************

Overview
========

Ralph has some mechanisms for automating deployment of servers. At the moment
only physical servers are supported, virtual server deployment is planned.

The deployment process has to perform several tasks:

* releasing any DNS names, DHCP entries and other resources associated with the old role of the server,
* assigning an IP address, together with corresponding DNS and DHCP entries,
* assigning the server to a new venture,
* assigning a new role for the server in Puppet,
* booting the server through PXE with a selected boot image and reinstalling its system.

In order to perform those tasks on a server, the deployment of a server goes
through a number of steps:

* open,
* in progress,
* done.

A newly started deployment always starts as "open". In that stage all the
deployment plugins are executed, clearing old DNS and DHCP entries, creating
new ones and assigning the server to a new Puppet role and venture. At that
point the status is changed to "in progress" and the server has to be rebooted
in order to install new operating system on it. As soon as the new system is
installed and Puppet applies the server's role, it sends a signal to Ralph that
switches the status of the deployment to "done". At this point the deployment
is finished and it is archived.


Interface
=========


Individual deployment
---------------------

Deployment can be started by clicking on a "deploy" button at the bottom of the
"info" tab of a device in Ralph. For the button to be visible, the device has
to have the "verified" checkbox checked. Once that is done, deployment is the
only way to change the device's venture and role.

The deployment form that appears lets you pick the desired new venture, role,
IP address and hostname for the server, as well as the MAC address that should
be used for booting it, and the boot image to boot from.

Bulk deployment
---------------

It is also possible to start deployments in bulk. The "add device" tab in the
"racks" section has an option called "servers" that lets you specify a CSV file
with all the required information, validates it and automatically fills in
missing information, and then starts deployments in bulk from it.

Programmatic Deployment of VMs
------------------------------------

The URL /api/add_vm/ can be used for a quick deployment of VMs. To perform it
you need to send a POST request with JSON, YAML or XML data. This data should
contain the following keys:

    network:
        The name of the network for the new machine
    management-ip:
        The IP of the container that will host the VM
    mac:
        The MAC address of VMs network interface
    venture:
        The symbol of the venture
    venture-role:
        The name of the venture role
        
Ralph will create a new VM and also configure powerdns and DHCP for it.


Plugins
=======

The deployment plugins are executed with the ``ralph deploy`` command regularly
by cron. That command iterates over all "open" deployments and executes all
plugins that haven't been yet successful for that deployment, but have all
their requirements ready.


Clean plugin
------------

The "clean" plugin is responsible for removing old information about a server
from the Ralph database and also from the DNS and DHCP configurations. It
performs the following tasks:

* remove all DHCP entries for the IP addresses associated with the server,
* remove all DNS entries for the IP addresses associated with the server,
* remove all DHCP entries for the MAC addresses associated with the server,
* disassociate all the IP addresses from the server,
* remove all software information associated with the server,
* remove all disk share information associated with the server,
* remove the operating system information associated with the server,
* disassociate all sub-devices,
* reset the uptime information,
* add a remark to the user comments for that server,
* associate the new IP address with the server.

This plugin should be always run at the beginning of deployment. It has no
requirements.


Role plugin
-----------

The "role" plugin is responsible for setting the server's new venture and role
in the Ralph's database.


DNS plugin
----------

The "dns" plugin is responsible for creating a DNS "A" entry, and the related
"PTR" entry, for the new IP address of the server.


DHCP plugin
-----------

The "dhcp" plugin is responsible for updating the DHCP entries in the Ralph
database, and then for waiting until all the DHCP servers have the updated
documentation. It will keep failing until all configured DHCP servers have
downloaded the new configuration.


Reboot plugin
-------------

This plugin is responsible for rebooting the physical server once all the other
plugins have finished their work. This plugin is currently disabled and the
servers have to be restarted manually.

Boot images
===========

At the end of the deployment process, the server needs to be restarted and it
has to boot one of the prepared boot images that installs a new operating
system. This is achieved using the bootp and PXE protocols.

To control that, Ralph lets you configure which boot images should be used for
every deployment, and then serves those images at the ``/pxe/`` URL. The exact
file being served depends on the IP that is requesting it.

The DHCP configuration generated by Ralph contains an additional header for the
IP addresses that have an active deployment. That header makes the server boot
from network, with a small Linux image (ePXE) that in turns downloads the
correct image from Ralph through HTTP and boots it. The exact value of that
header can be configured for every environment separately, as the ``next
server``.

Once the system installation is complete, the system should request
``/pxe/DONE/`` URL, which causes Ralph to mark the deployment as finished.
Ralph knows which deployment to mark as finished by the IP address of the
request.
