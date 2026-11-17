"""Read Telnet split banner with timeout. No editor dependency."""
import socket
import time

def receive_login_banner(sock, expected, *, budget=4.0):
    """Read past telnet IAC negotiation and split TCP packets to exact banner.

    Returns bytes actually received; a missing/incorrect version never passes.
    """
    deadline = time.monotonic() + budget
    payload = bytearray()
    while time.monotonic() < deadline and len(payload) < 65536:
        sock.settimeout(min(0.4, max(0.01, deadline - time.monotonic())))
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        if not chunk:
            break
        payload.extend(chunk)
        if expected in payload:
            break
    return bytes(payload)

