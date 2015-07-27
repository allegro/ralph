"""Low-level network utilities, silently returning empty answers in place of
domain-related exceptions."""


import socket

# moved from old ralph's source code
# OLD_PATH: ralph/util/network.py


def hostname(ip, reverse=False):
    """hostname(ip) -> 'hostname'

    `ip` may be a string or ipaddr.IPAddress instance.
    If no hostname known, returns None."""
    try:
        result = socket.gethostbyaddr(str(ip))
        return result[0] if not reverse else result[2][0]
    except socket.error:
        return None
