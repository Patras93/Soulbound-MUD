# -*- coding: utf-8 -*-
"""Owner-generated, one-time password recovery codes. Never write them to history."""
from network.protocol_gameplay_utils import normalize_lookup_text


class SessionPasswordRecoveryV1222Mixin:
    async def account_recovery_command_v1222(self, args=""):
        if not self.master_account_id:
            await self.send("Najpierw zaloguj się na swoje konto.")
            return
        action = normalize_lookup_text(args)
        # Both the short, recommended command and older help spelling work.
        if action in ("haslo kod", "hasło kod", "haslo generuj", "hasło generuj"):
            action = "kod"
        if action not in ("kod", "code", "generuj", "nowy"):
            await self.send(
                "Kod odzyskiwania hasła: wpisz konto kod. "
                "Kod zostanie pokazany tylko Tobie. Zapisz go poza grą. "
                "W menu logowania wybierz 4, gdy zapomnisz hasła."
            )
            return
        code = self.server.db.issue_password_recovery_v1222(self.master_account_id, "backup")
        if code is None:
            await self.send("Nie wygenerowano kodu. Odczekaj co najmniej minutę i spróbuj ponownie.")
            return
        await self.send(
            "TWÓJ JEDNORAZOWY KOD ODZYSKIWANIA: " + code + ". "
            "Zapisz go prywatnie poza grą. Poprzedni kod jest nieważny. "
            "Kod jest ważny przez 365 dni albo do wykorzystania.",
            history_store=False,
        )

    async def account_email_command_v1223(self, args=""):
        # Compatibility for older command registries: e-mail is not a recovery path.
        await self.account_recovery_command_v1222("")
