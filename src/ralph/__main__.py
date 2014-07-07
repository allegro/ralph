#!/usr/bin/env python
import os
import sys

try:
    from raven.contrib.django.raven_compat.models import client as raven_client
except ImportError:
    raven_client = None  # noqa


def ubuntu_1020872_workaround():
    """Workaround for spurious "Error opening file for reading: Permission
    denied" printed to stderr while importing _imaging due to libjpeg not being
    able to open /proc/self/auxv on a setcapped `python` process. Reported as
    Ubuntu bug https://bugs.launchpad.net/libjpeg-turbo/+bug/1020872.
    """
    dup = os.dup(2)
    os.close(2)
    try:
        import _imaging  # noqa
    except ImportError:
        from PIL import Image  # noqa
        """
        Newer version of Pillow doesn't have _imaging module. Use PIL instead.
        Basically, we need to initialize Pillow, which does internally ctypes.dlopen('libjpeg.so.0.8')
        which further opens /dev/proc/auxv to optimize JPEG decoding.
        Ralph setup needs currently setcap net_raw on python process, which doesn't works seamlesly
        with libjpeg turbo optimization, which produces werid Permission denied error output problem
        from actually library below, not python code at all.
        What we are trying to do is a workaround to reset error stream
        (duplicate error output descriptor, and clean-up).

        The real solution is just to run rqworker processes as root process or higher level permissions
        :-)
        """
    finally:
        os.dup2(dup, 2)
        try:
            sys.__stderr__.close()
            sys.stderr.close()
        except IOError:
            pass
        sys.__stderr__ = sys.stderr = os.fdopen(2, 'a')


def main():
    if sys.platform.startswith('linux'):
        ubuntu_1020872_workaround()

    os.environ["DJANGO_SETTINGS_MODULE"] = "ralph.settings"

    from django.core.management import execute_from_command_line

    sys.argv[0] = os.path.dirname(__file__)
    try:
        execute_from_command_line(sys.argv)
    except Exception:
        if raven_client:
            raven_client.captureException()
        raise


if __name__ == "__main__":
    main()
