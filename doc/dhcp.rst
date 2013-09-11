DHCP configuration
******************

Ralph can generate configuration for your DHCP servers. Unfortunately, we
didn't find any DHCP server that could use a database for storing its
configuration directly, so to keep the configuration updated, you will need to
generate it from Ralph periodically and reload your DHCP server when it
changes. There is a script called ``ralph_dhcp_agent.py`` distributed with
Ralph in the ``contrib`` directory that makes it easier to do.

Ralph DHCP agent
================

This script is supposed to be called periodically by cron. It will download a
new DHCP configuration for the server on which it runs from Ralph, compare its
date with the date of the current configuration, and restart your DHCP server
if the downloaded configuration is newer.


Configured DHCP servers
=======================

Ralph can optionally keep a list of all DHCP servers in its data centers. When
a DHCP server that is on that list downloads a fresh DHCP configuration from
Ralph, Ralph will note this fact in the database. This is later used during
server deployment to wait for all DHCP servers to update their configuration.
If a DHCP server is not on the list, Ralph will not wait for it to update
before proceeding with deployment.

Importing and exporting DHCP configuration
==========================================

You can use the ``dhcpimport`` and ``dhcpexport`` Ralph commands to import or
export DHCP entries.
