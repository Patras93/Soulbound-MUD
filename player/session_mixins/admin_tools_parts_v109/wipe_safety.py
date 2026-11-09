"""Wydzielone metody oryginalne v109 — bez zmian mechaniki.

Testy zgodnosci porownuja AST z poprzednia paczka, nie tylko nazwy.
"""
# -*- coding: utf-8 -*-

class AdminWipeSafetyV109Mixin:
    async def wipe_command(self, args=""):
            if not self.is_admin():
                await self.send("Nieznana komenda. Wpisz help.")
                return
            norm = self.normalize_description_query(args)
            if norm.startswith("naprawione"):
                await self.admin_error_cleanup_shortcut_v1405(norm)
                return
            own_tokens = ("moje postacie", "my characters")
            all_tokens = ("wszystkie postacie", "all characters")
            confirmed_pl = norm.endswith(" potwierdzam")
            confirmed_en = norm.endswith(" confirm")
            if not (confirmed_pl or confirmed_en):
                await self.send(
                    "WIPE wymaga potwierdzenia. Konta NIE zostaną usunięte. "
                    "Użyj: wipe moje postacie POTWIERDZAM albo wipe wszystkie postacie POTWIERDZAM."
                )
                return
            scope = norm.rsplit(" ", 1)[0]
            if scope not in own_tokens + all_tokens:
                await self.send("Nieprawidłowy zakres wipe.")
                return

            if scope in own_tokens:
                target_masters = {int(self.master_account_id)}
            else:
                target_masters = {
                    int(row["id"])
                    for row in self.server.db.conn.execute(
                        "SELECT id FROM accounts WHERE id NOT IN ("
                        "SELECT character_account_id FROM account_characters "
                        "WHERE character_account_id<>master_account_id)"
                    ).fetchall()
                }

            # Inne aktywne sesje z wipe zostają rozłączone bez zapisu usuwanej postaci.
            for session in list(self.server.sessions):
                if session is self or session.master_account_id not in target_masters:
                    continue
                try:
                    await session.send("ADMIN WIPE: postacie zostały wyczyszczone. Konto pozostaje. Połącz się ponownie.")
                    await session.prepare_character_wipe()
                    session.closed = True
                    session.writer.close()
                except Exception:  # AUDIT_INTENTIONAL_PASS: target session may already be disconnected during wipe
                    pass

            await self.prepare_character_wipe()
            if scope in own_tokens:
                removed = self.server.db.wipe_characters_for_master(self.master_account_id)
            else:
                removed, _masters = self.server.db.wipe_all_characters_preserve_accounts()
            # Wipe składu drużyn to tylko stan sesyjny.
            self.server.parties.clear()
            self.server.party_invites.clear()
            self.server.party_protectors.clear()
            self.server.party_goals.clear()
            self.server.party_routes_v1193.clear()
            self.server.party_ready_checks.clear()
            await self.send(f"WIPE POSTACI zakończony. Usunięto postaci: {removed}. Konta i hasła zachowane.")
            selected = await self.character_selection_flow()
            if selected is True:
                await self.enter_world()

