.. _develop_plugins:

===========================
Writing custom SCAN plugins
===========================

PUSH - 3rd party scripts (REST API interface)
---------------------------------------------
Just push some hardware data using your favorite tool/language and Ralph Core
will reconcilate data and allow you to save it.
  - use any language you want
  - can store plugins outside of Ralph Core system
  - more compatibility across new Ralph releases
  - PUSH mode


PULL - Generic SCAN plugins
---------------------------
Use this if your hardware is a generic one, and can be periodically scanned
alongside other existing plugins like http, snmp, ping.

First-class SCAN plugin allows you to reuse some features like:
  - you don't have to reinvent ping scans, snmp scanning
  - Python knowledge required
  - strictly integrated with k

