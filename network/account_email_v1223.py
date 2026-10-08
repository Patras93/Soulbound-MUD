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
    return all(os.getenv(key, "").strip() for key in (
        "SOULBOUND_SMTP_HOST", "SOULBOUND_SMTP_USER", "SOULBOUND_SMTP_PASSWORD", "SOULBOUND_SMTP_FROM"
    ))


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
    if not smtp_ready_v1223():
        raise RuntimeError("Poczta SMTP nie jest skonfigurowana")
    if normalized_email_v1223(recipient) is None:
        raise ValueError("Nieprawidlowy odbiorca")
    sender = normalized_email_v1223(os.environ["SOULBOUND_SMTP_FROM"])
    if sender is None:
        raise RuntimeError("Nieprawidlowy adres SOULBOUND_SMTP_FROM")
    host = os.environ["SOULBOUND_SMTP_HOST"].strip()
    mode = os.getenv("SOULBOUND_SMTP_MODE", "starttls").strip().lower()
    if mode not in ("ssl", "starttls"):
        raise RuntimeError("SMTP wymaga SSL lub STARTTLS")
    port = int(os.getenv("SOULBOUND_SMTP_PORT") or ("465" if mode == "ssl" else "587"))
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)
    context = ssl.create_default_context()
    if mode == "ssl":
        with smtplib.SMTP_SSL(host, port, timeout=12, context=context) as connection:
            connection.login(os.environ["SOULBOUND_SMTP_USER"], os.environ["SOULBOUND_SMTP_PASSWORD"])
            connection.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=12) as connection:
            connection.ehlo()
            connection.starttls(context=context)
            connection.ehlo()
            connection.login(os.environ["SOULBOUND_SMTP_USER"], os.environ["SOULBOUND_SMTP_PASSWORD"])
            connection.send_message(msg)


async def send_code_v1223(recipient, purpose, code):
    if purpose == "register":
        subject = "Soulbound - potwierdzenie adresu e-mail"
        body = "Kod potwierdzenia nowego konta Soulbound: " + code + "\nWazny 10 minut. Jesli to nie Ty, zignoruj wiadomosc."
    elif purpose == "attach":
        subject = "Soulbound - potwierdzenie adresu konta"
        body = "Kod przypisania adresu e-mail do konta Soulbound: " + code + "\nWazny 10 minut. Jesli to nie Ty, zignoruj wiadomosc."
    else:
        subject = "Soulbound - resetowanie hasla"
        body = "Jednorazowy kod resetowania hasla Soulbound: " + code + "\nWazny 15 minut. W menu logowania wybierz 4, potem reset przez e-mail. Jesli to nie Ty, zignoruj wiadomosc."
    await asyncio.to_thread(_send_mail_sync_v1223, recipient, subject, body)
