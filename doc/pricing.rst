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
by setting a manual price on the device -- it will be then used in place of
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

For details see the descriptiosn of pricing of specific kinds of devices below.

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

This is calculated from *quoted price* increased by *price margin* and divided
by *deprecation time*. This :index:`cost` is then used everywhere to calculate
the device's usage costs. It's what your customers will see.

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

For a blade system, the process is similar. First, the price of the system is
calculated as normal, and then the *m/n* of the chassis price is added to it.


:index:`Virtual servers`
------------------------

The price of virtual server's CPU is calculated as *1/n* of the sum of prices
of the CPUs in the hypervisor, where *n* is the sum of all virtual CPUs on
all the virtual machines running on that hypervisor.

The price of virtual server's memory is calculated normally, the memory model
is set to "Virtual Memory" and you can set a price per 1GB of it.

The disk space of a virtual server is not included in its price -- it's assumed
that it only contains the base system of the server, and all relevant storage
is done on the disk shares connected to it.

The disk shares are counted normally, with the exception that if not a whole
disk share is used by the virtual machine's disk image, then only the part
that is used is included in the price.

:index:`Virtual server hypervisors`
-----------------------------------

The price of a virtual server hypervisor is calculated normally, but then the
total prices of its virtual machines are subtracted from it.

:index:`Storage`
----------------

The price of storage is calculated normally, and then the prices of all the
:index:`disk shares` that are mounted somwehere (and thus their price is
already included in the price of whatever device they are mounted on) are
subtracted from it.
