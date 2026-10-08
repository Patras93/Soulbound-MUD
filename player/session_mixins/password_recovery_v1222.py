# -*- coding: utf-8 -*-
"""Account recovery code for an authenticated player. Never store secret in chat history."""

from network.protocol_gameplay_utils import normalize_lookup_text, verify_password
from network.account_email_v1223 import (
    normalized_email_v1223, smtp_ready_v1223, send_code_v1223,
    allow_verification_send_v1223,
)
import secrets
import time
import hmac
import sqlite3
import smtplib


class SessionPasswordRecoveryV1222Mixin:
    async def account_recovery_command_v1222(self, args=""):
        if not self.master_account_id:
            await self.send("Najpierw zaloguj się na konto.")
            return
        action = normalize_lookup_text(args)
        if action not in ("kod", "code", "generuj", "nowy"):
            await self.send(
                "Odzyskiwanie hasła: wpisz odzyskaj haslo kod, aby utworzyć zapasowy "
                "kod odzyskiwania. Zapisz go prywatnie poza grą. Gdy zapomnisz hasła, "
                "w menu głównym wybierz 4 i podaj kod."
            )
            return
        code = self.server.db.issue_password_recovery_v1222(self.master_account_id, "backup")
        if code is None:
            await self.send("Odczekaj minutę przed wygenerowaniem kolejnego kodu.")
            return
        await self.send(
            "Twój zapasowy kod odzyskiwania (użycie jednorazowe): " + code + ". "
            "Zapisz go poza grą. Poprzedni kod zapasowy jest teraz nieważny. "
            "Kod wygaśnie za 365 dni.", history_store=False,
        )


    async def account_email_command_v1223(self, args=""):
        """Authenticated account's verified e-mail, never a public character field."""
        if not self.master_account_id:
            await self.send("Najpierw zaloguj się.")
            return
        tokens = str(args or "").strip().split(maxsplit=1)
        action = normalize_lookup_text(tokens[0]) if tokens else ""
        current = self.server.db.verified_account_email_v1223(self.master_account_id)
        if action in ("email", "e mail") and len(tokens) > 1:
            tokens = tokens[1].split(maxsplit=1)
            action = normalize_lookup_text(tokens[0]) if tokens else ""
        if action not in ("ustaw", "zmien", "zmień", "dodaj", "set"):
            await self.send("E-mail konta: " + ("potwierdzony" if current else "nieustawiony") + ".")
            await self.send("Aby dodać albo zmienić: konto email ustaw / emailkonto ustaw.")
            return
        if not smtp_ready_v1223():
            await self.send("E-mail niedostępny: administrator musi skonfigurować SMTP.")
            return
        password = await self.ask("Potwierdź obecne hasło konta: ")
        if password is None:
            return
        owner = self.server.db.conn.execute(
            "SELECT password_salt,password_hash FROM accounts WHERE id=?", (int(self.master_account_id),)
        ).fetchone()
        if owner is None or not verify_password(password, owner["password_salt"], owner["password_hash"]):
            await self.send("Nieprawidłowe hasło. Niczego nie zmieniono.")
            return
        raw_email = await self.ask("Nowy adres e-mail (0 anuluje): ")
        if raw_email is None or raw_email.strip() == "0":
            return
        email = normalized_email_v1223(raw_email)
        if email is None:
            await self.send("Nieprawidłowy adres e-mail.")
            return
        if self.server.db.email_taken_v1223(email) and current != email:
            await self.send("Adres jest już używany przez inne konto.")
            return
        peer = self.writer.get_extra_info("peername") if getattr(self, "writer", None) else None
        peer_ip = peer[0] if isinstance(peer, tuple) and peer else None
        if not allow_verification_send_v1223(email, peer_ip):
            await self.send("Limit wysyłki kodów. Spróbuj ponownie za 15 minut.")
            return
        code = secrets.token_hex(4).upper()
        start = time.monotonic()
        try:
            await send_code_v1223(email, "attach", code)
        except (OSError, RuntimeError, ValueError, TimeoutError, smtplib.SMTPException):
            await self.send("Nie udało się wysłać kodu. Adres nie został zmieniony.")
            return
        await self.send("Kod wysłany. Masz 10 minut i 5 prób.")
        for _ in range(5):
            entered = await self.ask("Kod potwierdzenia (0 anuluje): ")
            if entered is None or entered.strip() == "0" or time.monotonic() - start > 600:
                break
            if hmac.compare_digest(entered.strip().upper(), code):
                try:
                    self.server.db.attach_verified_email_v1223(self.master_account_id, email)
                except (sqlite3.IntegrityError, ValueError):
                    await self.send("Adres jest już zajęty. Poprzedni e-mail pozostaje bez zmian.")
                    return
                await self.send("E-mail konta potwierdzony. Możesz odzyskiwać hasło przez pocztę.")
                return
            await self.send("Nieprawidłowy kod.")
        await self.send("Nie potwierdzono adresu. Poprzedni e-mail pozostaje bez zmian.")
