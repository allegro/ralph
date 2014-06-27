=====
Ralph
=====


Ralph consists of 3 submodules:

Ralph Core
**********
Ralph Core(DCIM and CMDB) acts as a base system for Ralph applications.
It is the database of Networks, IP Addresses, Racks, and discovered hardware.

It allows you to:
	* scan networks automatically through periodic or manual scans.
	* deploy servers by generating appropriate DNS/DHCP configs and uses I/PXE method.
	* see relations between Configuration Items using CMDB view interface


Ralph Assets
************
This submodule provides advanced Asset management system which has following features:
	* manual inventory system
	* can be using alongside Ralph Core discovery using reconciliation technique
	* covers complete life cycle of asset from purchase to utilization
	* gives ability to generating custom defined PDF documents (hardware assignments printouts for example)
	* integrated assets license management
	* integrated basic hardware support/contracts management
	* easy & usable module for generic inventory tasks


Ralph Pricing "Scrooge"
***********************
This submodule provides flexible billing and financial reporting subsystem which can:
	* calculate TCO of Services using complex utilization of bare metal costs,
	  IT Support work time, virtualization costs
	* integrate OpenStack billings with hardware costs
	* gather historical data every day to safely inspect trends over time

