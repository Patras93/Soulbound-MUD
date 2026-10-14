# -*- coding: utf-8 -*-
"""Verified account e-mail for registration and recovery (no third-party dependencies)."""

import asyncio
from collections import deque
import hashlib
import time
from email.message import EmailMessage
import os
import re
import smtplib
import ssl


EMAIL_PATTERN_V1223 = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$")


def normalized_email_v1223(value):
    email = str(value or "").strip().lower()
    if len(email) > 254 or not EMAIL_PATTERN_V1223.fullmatch(email) or ".." in email:
        return None
    return email


def smtp_ready_v1223():
    """Mail recovery disabled irrespective of server environment variables."""
    return False


# Volatile rate limits: no mailbox or IP saved to the database/logs.
_EMAIL_SEND_LIMITS_V1223 = {}


def allow_verification_send_v1223(address, peer=None, *, now=None):
    now = time.monotonic() if now is None else float(now)
    keys = [("mail", hashlib.sha256(address.encode("utf-8")).hexdigest(), 2)]
    if peer:
        keys.append(("peer", hashlib.sha256(str(peer).encode("utf-8")).hexdigest(), 5))
    # Keep memory bounded on long-running servers.
    if len(_EMAIL_SEND_LIMITS_V1223) > 10000:
        for key in list(_EMAIL_SEND_LIMITS_V1223):
            q = _EMAIL_SEND_LIMITS_V1223[key]
            if not q or now - q[-1] > 900:
                del _EMAIL_SEND_LIMITS_V1223[key]
    for kind, ident, limit in keys:
        q = _EMAIL_SEND_LIMITS_V1223.setdefault((kind, ident), deque())
        while q and now - q[0] >= 900:
            q.popleft()
        if len(q) >= limit:
            return False
    for kind, ident, _ in keys:
        _EMAIL_SEND_LIMITS_V1223[(kind, ident)].append(now)
    return True


def _send_mail_sync_v1223(recipient, subject, body):
    raise RuntimeError("Metoda odzyskiwania przez pocztę została wyłączona.")


async def send_code_v1223(recipient, purpose, code):
    raise RuntimeError("Metoda odzyskiwania przez pocztę została wyłączona.")
