Pricing mechanisms
==================

The way Ralph calculates device prices and costs seems to be very simple at
first, but has a lot of special cases. You can find the detailed description
of the formulas used here.

Basic terms
***********

:index:`Auto price`
-------------------

:index:`Raw price` is the sum of prices of all components of the device, together
with the price of the device itself. It includes all the parts inside it,
such as processors, memory, extension cards, disks, etc. It also includes the
prices of any mounted disk shares and installed software.

:index:`Manual price`
---------------------

Sometimes the automatically calculated price is not right. You can override it
by setting a manual price on the device -- it will then be used in place of
the *auto price*.

:index:`Quoted price`
---------------------

This is automatically calculated price. It starts with the *auto price* (or
*manual price* if set), but then prices of several items are subtracted or
added, depending on the specific cases.

For example, for a blade server, a fraction of the price of its chassis is
added -- and the same fraction is subtractred from the chassis' price, so that
a full blade system chassis should have price of 0. Another special case is a
virtual server hypervisor, which has the prices of its virtual server instances
subtracted from its own price.

For details see the descriptions of pricing of specific kinds of devices below.

:index:`Price margin`
---------------------

The :index:`margin` tells how much more the customers need to pay for using the
devices, apart from the basic price of the device itself. It includes the
maintenance costs, the electricity bill, the data center rent, etc. You usually
set the margin on a venture, so that it applies to all devices in that venture,
but you can also set it on individual devices -- then it will override the
venture default.

:index:`Deprecation time`
-------------------------

:index:`Deprecation` time tells how long you plan to use the device. The
assumption is that during that time the device should "earn for itself" -- that
is used to calculate the monthly cost of the device.

:index:`Monthly cost`
---------------------

This is calculated from the device's *quoted price* increased by its *price
margin* and divided by its *deprecation time*. This :index:`cost` is then used
everywhere to calculate the usage costs for the device. It's what your customers
will see.

Device pricing details
**********************

:index:`Blade systems`
----------------------

The price of a blade system :index:`chassis` is calculated as follows: we start
with the *quoted price* (or *manual price*, if set). Next, for every blade
server in the chassis, we subtract *m/n* of the price, where *m* is the number
of slots that the blade server occupies, and *n* is the total number of slots
in the chassis.

:index:`Blade servers`
----------------------

For a blade server, the process is similar. First, the price of the server is
calculated as normal, and then the *m/n* of the chassis price is added to it.


:index:`Virtual servers`
------------------------

The disk shares that are mounted from the hypervisor are counted as used by the
virtual servers, with the exception that if not a whole disk share is used by
the virtual machine's disk image, then only the part that is used is included
in the price.

:index:`Virtual server hypervisors`
-----------------------------------

The price of a virtual server hypervisor is calculated normally, but then the
total prices of its virtual machines are subtracted from it.

:index:`Remote storage`
-----------------------

The price of storage is calculated normally, and then the prices of all the
:index:`disk shares` that are mounted somewhere (and thus their price is
already included in the price of whatever device they are mounted on) are
subtracted from it.

:index:`Default disks, CPUs and memory`
---------------------------------------

When a server is missing the information about its hard disk drives, memory
chips or processors, the pricing algorithm estimates their values by taking
information collected at the operating system level: the amount of available
disk space, the amount of free system memory and the number of CPU cores
available. The prices for those are calculated based on the "OS Detected
Storage", "OS Detected Memory" and "OS Detected CPU" model groups, if they
exist in the catalog (they have to be created manually).

If the appropriate model groups don't exists in the catalog, or there is no
information available from the operating system, Ralph assumes that the server
has a default memory, disk and CPU -- if it finds "Default Memory", "Default
Disk" or "Default CPU" model groups in the catalog.

Finally, if none of this information is available, the missing components are
not included in the pricing.


Pricing Groups
**************

Sometimes it is not possible to calculate the prices of all devices of a
specified type in the same way. In that case, you can use pricing groups in the
catalog section to specify different rules for some of your devices.

You need to create a separate pricing group for each month, with the list of
devices that are going to be affected, a list of different variables for them,
and a list of components and formulas for calculating their prices. The
formulas can use the standard arithmetic operators (``+``, ``-``, ``*``, ``/``,
etc.) as well as variables defined for the given group, and a special variable
``size`` that is taken from the component itself. In the future, more special
variables can be introduced.

For the moment, the only components that can be handled this way are the disk
shares.

Because manual creation of all those pricing groups for every month can be
tedious, there are two mechanisms that make it easier to create them. If you
check the "Clone the last group with that name" checkbox, and there is a group
with the same name for any earlier month, its contents will be copied to the
newly created group. Alternatively, you can upload a CSV file with the
definitions of the devices and variables for the group. The file should have
the following format::

    sn; variable1; variable2; variable3
    102501X;    1.00;   2;      -3.1
    C12324;    1.00;   2;      -3.1
    242402;    1.00;   2;      -3.1

It's important for the contents of the first cell in the CSV file to have the
string "sn" in it, signifying that the column lists serial numbers of the
devices. In the future, different ways of specifying the devices may be added.

