The device browser
==================

The main feature of the Ralph web interface is the browser for your discovered
devices. Depending on your needs and permissions, you can browse them
in five ways:

* The "racks" browser lets you see the physical organisation of your
  datacenter, indicating where every device is located.
* The "ventures" browser lets you browse by the organisations that own
  the devices, and by the services to which they belong.
* The "networks" browser enables you to see your datacenter from the
  point of view of the network addresses.
* The "CMDB" browser displays the devices and other elements relevant to
  change management, together with their relations and changes.
* Finally, the "advanced search" browser lets you create custom lists of
  devices based on many attributes set on them, such as name, model,
  components, serial number or change history.

Viewing devices
***************

No matter which browser you use, you will see a tabbed view with a list of the
devices. Each of the tabs will display a different set of columns in the list,
and after clicking on a device name, different form with information about that
device.

:index:`Info`
-------------

This tab displays the general information about the device, such as its name,
model, serial number and barcode, owner and role, physical position etc. It
also displays a number of links to related devices and pages, depending on the
type of the device, such as virtual machine's hypervisor or blade server's
management address.

:index:`Components`
-------------------

This tab shows the information about detected contents of the device.
It lists the model and serial numbers of all of its physical components,
such as processors, memory, disks and extension cards. It also lists the
software that was detected on the device, together with its versions.


:index:`Addresses`
------------------

This tab shows everything that is related to network: the list of IP addresses
assigned to the device, the relevant DHCP and DNS configuration entries, and
the list of relevant :index:`loadbalancer` pools, together with their state.

:index:`History`
----------------

In this tab you can see the history of all changes to the device in the
database, together with dates, comments and people responsible for the change.
It's useful when you need to track what happened with the device in the past.

:index:`Discover`
-----------------

Using this tab, you can force re-running of the discovery process for any of
the device's IP addresses (or even enter a custom IP address by hand). It will
show you the logs from the discovery process as it happens.

.. Note::
    Note that this is equivalent to running the discovery from a command line
    on the server which hosts the web application -- the task is not sent to
    external workers. If your workers are in different private networks or have
    different access to the devices you are managing, then the results of
    manual discovery may be different from the automatic discovery done by the
    workers.

:index:`Roles`
--------------

Visible only in the "Ventures" section, this tab shows you all the device roles
defined in that venture.

:index:`Venture`
----------------

Only displayed in the "Ventures" section, shows information about the currently
selected venture. You can see a summary of costs for selected time period,
together with a graph showing how the costs changed in time.


:index:`CMDB`
-------------

This tab displays information relevant to change management. More details in the
CMDB documentation.


Editing devices
***************

Depending on your permissions, you may be able to change the attributes of
devices that you are viewing. Every time you make a change, you have to
provide a comment describing your change for the change history.

Once any of the fields have been changed manually, a small :index:`hand icon`
is displayed next to that field. That means, that the value of that field will
not be updated automatically now -- to not overwrite the :index:`manual
changes`.  You can click on that icon in order to remove it and allow automatic
changes of the field.

There's one more restriction here - when a device is assigned to an asset, you
can not change its position fields (i.e. parent, dc, rack, position,
orientation). In order to do that, you should use "Assets" module instead.
This should be considered as a temporary workaround, because in the future,
position will be stored only in the "Assets" module.
