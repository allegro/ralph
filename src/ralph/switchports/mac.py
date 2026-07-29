"""MAC address arithmetic helpers (sequence neighbours).

Pure functions with no DB or netmaker coupling. Used by the demo import to
guess the adjacent interface of a dual-port NIC.
"""

from django.core.exceptions import ValidationError


def next_mac(mac: str) -> str:
    """
    Returns the next MAC address in sequence.
    >>> next_mac('00:1A:2B:3C:4D:5E')
    '00:1A:2B:3C:4D:5F'
    >>> next_mac('FF:FF:FF:FF:FF:FF')
    '00:00:00:00:00:00'
    """
    try:
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        next_mac_bytes = (int.from_bytes(mac_bytes, byteorder="big") + 1) % (1 << 48)
        next_mac_str = ":".join(
            f"{(next_mac_bytes >> (i * 8)) & 0xFF:02X}" for i in reversed(range(6))
        )
        return next_mac_str
    except ValueError:
        raise ValidationError(f"Invalid MAC address format: {mac}")


def previous_mac(mac: str) -> str:
    """
    Returns the previous MAC address in sequence.
    >>> previous_mac('00:1A:2B:3C:4D:5E')
    '00:1A:2B:3C:4D:5D'
    >>> previous_mac('00:00:00:00:00:00')
    'FF:FF:FF:FF:FF:FF'
    """
    try:
        mac_bytes = bytes.fromhex(mac.replace(":", ""))
        previous_mac_bytes = (int.from_bytes(mac_bytes, byteorder="big") - 1) % (
            1 << 48
        )
        previous_mac_str = ":".join(
            f"{(previous_mac_bytes >> (i * 8)) & 0xFF:02X}" for i in reversed(range(6))
        )
        return previous_mac_str
    except ValueError:
        raise ValidationError(f"Invalid MAC address format: {mac}")
