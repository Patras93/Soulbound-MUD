"""Explicit ownership transfer of the listener opened by the server bootstrap."""
from __future__ import annotations

_boot_socket = None


def register_boot_socket(listener):
    """Publish the existing listener exactly once before runtime construction."""
    global _boot_socket
    if _boot_socket is not None:
        raise RuntimeError("A bootstrap listener is already registered")
    _boot_socket = listener


def take_boot_socket():
    """Transfer the listener to the asyncio server; subsequent calls return None."""
    global _boot_socket
    listener, _boot_socket = _boot_socket, None
    return listener
