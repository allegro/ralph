Notifications
*************

Overview
========

Notifications is a simple app to send and archive your emails. Some features:

* send email asynchronoulsy by rq queue,
* supports HTML and TXT emails,
* supports Django template engine to render emails,
* supports max retries.


Example of use
==============
Simple example::

    from ralph.notifications import send_email

    send_email(
        receivers=['john.doe@example.com', 'bill@example.com'],
        sender='notifications@ralph.local',
        subject='New device was discovered',
        html_template='simple',
        txt_template='simple',
        variables={'content': 'Notifications content...'},
    )


Configuration
=============

Notifications provides two extra settings:

* ``NOTIFICATIONS_MAX_ATTEMPTS`` -- max attemps (default ``10``)
* ``NOTIFICATIONS_QUEUE_NAME`` -- name of rq queue which it is use for sending email (default ``default``)
